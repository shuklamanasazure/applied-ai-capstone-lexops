"""Qdrant storage for firm playbooks and approved precedents."""

# Create UUIDs for stable point IDs.
import uuid
# Import path helpers for corpus scanning.
from pathlib import Path

# Import Qdrant client and model definitions.
from qdrant_client import QdrantClient, models

# Import application configuration and LLM embeddings.
from .config import settings
from .llm import LLMService


class QdrantStore:
    """Own Qdrant collection lifecycle, indexing and retrieval."""

    def __init__(self, llm: LLMService) -> None:
        # Create the client once and reuse it for all requests.
        self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        # Keep embeddings behind the LLM service so the vector model is replaceable.
        self.llm = llm

    def ensure_collection(self, recreate: bool = False) -> None:
        # Recreate is convenient for deterministic assignment demonstrations.
        if recreate and self.client.collection_exists(settings.qdrant_collection):
            self.client.delete_collection(settings.qdrant_collection)
        # Create the collection only when it does not already exist.
        if not self.client.collection_exists(settings.qdrant_collection):
            self.client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=models.VectorParams(
                    size=settings.embedding_dimension,
                    distance=models.Distance.COSINE,
                ),
            )

    def _chunk_markdown(self, text: str, chunk_size: int = 1800, overlap: int = 200) -> list[str]:
        # Normalize line endings so chunking is deterministic across operating systems.
        text = text.replace("\r\n", "\n").strip()
        # Return nothing for empty files.
        if not text:
            return []
        # Use simple character chunks for a learner-friendly implementation.
        chunks: list[str] = []
        # Start at the beginning of the document.
        start = 0
        # Continue until the entire document has been consumed.
        while start < len(text):
            # Compute the next chunk boundary.
            end = min(start + chunk_size, len(text))
            # Store the current chunk.
            chunks.append(text[start:end])
            # Stop after the final chunk.
            if end == len(text):
                break
            # Move forward while retaining a small overlap for context continuity.
            start = end - overlap
        # Return all generated chunks.
        return chunks

    def _infer_metadata(self, path: Path, corpus_dir: Path, index_data: dict | list) -> dict:
        # Calculate a stable relative path for traceability.
        relative = str(path.relative_to(corpus_dir))
        # Start with generic metadata available for every document.
        metadata = {"source_file": relative, "source_type": "organizational_knowledge"}
        # Normalize both common index.json shapes: one object or a list of objects.
        if isinstance(index_data, dict) and "slug" in index_data:
            index_items = [index_data]
        elif isinstance(index_data, dict):
            index_items = list(index_data.values())
        else:
            index_items = index_data
        # Try to map the filename to an index.json record.
        for item in index_items:
            if not isinstance(item, dict):
                continue
            # Match either an explicit path or a slug contained in the filename.
            slug = str(item.get("slug", ""))
            if relative == item.get("path") or slug and slug in path.stem:
                metadata.update({k: v for k, v in item.items() if isinstance(v, (str, int, float, bool))})
                break
        # Infer clause type from common names when index.json does not provide it.
        if "clause_type" not in metadata:
            lower = f"{path.stem} {metadata.get('title', '')}".lower()
            for clause in ["liability", "termination", "indemnification", "governing_law", "renewal", "confidentiality"]:
                if clause.replace("_", " ") in lower or clause in lower:
                    metadata["clause_type"] = clause
                    break
        # Identify likely approved redlines from filename/path wording.
        if any(word in relative.lower() for word in ["redline", "approved", "precedent"]):
            metadata["source_type"] = "approved_redline"
        # Return metadata used as Qdrant payload.
        return metadata

    def ingest(self, corpus_dir: str | None = None, recreate: bool = False) -> int:
        # Resolve the corpus path from the request or configuration.
        root = Path(corpus_dir or settings.corpus_dir)
        # Stop with a useful error when the expected directory is missing.
        if not root.exists():
            raise FileNotFoundError(f"Corpus directory does not exist: {root}")
        # Read index.json when present so titles/slugs can be preserved.
        index_path = root / "index.json"
        index_data = {}
        if index_path.exists():
            import json
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
        # Ensure the target collection is ready.
        self.ensure_collection(recreate=recreate)
        # Find all Markdown files recursively.
        files = sorted(root.rglob("*.md"))
        # Keep a running count for the API response.
        indexed = 0
        # Process files one at a time to keep memory usage low.
        for path in files:
            # Read the Markdown content.
            text = path.read_text(encoding="utf-8", errors="ignore")
            # Split large documents into retrieval-sized chunks.
            chunks = self._chunk_markdown(text)
            # Build metadata once per file.
            metadata = self._infer_metadata(path, root, index_data)
            # Embed all chunks from one file together to reduce API calls and token overhead.
            vectors = self.llm.embed(chunks) if chunks else []
            # Add each chunk independently so search can return precise evidence.
            for chunk_number, (chunk, vector) in enumerate(zip(chunks, vectors)):
                # Add chunk-level metadata for filtering and citation.
                payload = {**metadata, "chunk_number": chunk_number, "text": chunk}
                # Create a unique Qdrant point ID.
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{relative_key(path, root)}:{chunk_number}"))
                # Upsert the vector and payload.
                self.client.upsert(
                    collection_name=settings.qdrant_collection,
                    points=[models.PointStruct(id=point_id, vector=vector, payload=payload)],
                    wait=True,
                )
                # Increment the count after successful storage.
                indexed += 1
        # Return number of indexed chunks.
        return indexed

    def search(self, query: str, clause_type: str | None, counterparty_id: str | None, top_k: int) -> list[dict]:
        # Create a query embedding using the same model as indexing.
        vector = self.llm.embed([query])[0]
        # Build Qdrant filters only when filters are supplied.
        must = []
        if clause_type:
            must.append(models.FieldCondition(key="clause_type", match=models.MatchValue(value=clause_type)))
        if counterparty_id:
            must.append(models.FieldCondition(key="counterparty_id", match=models.MatchValue(value=counterparty_id)))
        # Query the nearest chunks using the current Qdrant API.
        response = self.client.query_points(
            collection_name=settings.qdrant_collection,
            query=vector,
            query_filter=models.Filter(must=must) if must else None,
            limit=top_k,
            with_payload=True,
        )
        # Convert Qdrant records into application-independent dictionaries.
        return [
            {
                "source": "qdrant",
                "score": point.score,
                "content": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"},
            }
            for point in response.points
        ]


def relative_key(path: Path, root: Path) -> str:
    # Return a normalized relative path for deterministic UUID generation.
    return str(path.relative_to(root)).replace("\\", "/")
