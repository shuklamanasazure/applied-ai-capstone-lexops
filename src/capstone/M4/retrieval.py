"""Progressive retrieval: dense baseline, BM25, RRF fusion, and reranking."""

import re  # Tokenize clauses consistently.
from collections import defaultdict  # Aggregate reciprocal-rank scores.
from pathlib import Path  # Configure local Qdrant persistence.
from rank_bm25 import BM25Okapi  # Sparse lexical baseline.
from qdrant_client import QdrantClient  # Dense vector index and local persistence.
from fastembed import TextEmbedding  # Public embedding API for document and query vectors.
from qdrant_client.models import Distance, PointStruct, VectorParams  # Qdrant collection definitions.
from capstone.M4.corpus import Chunk  # Reuse traceable corpus records.


COLLECTION = "lexops_playbook_chunks"  # Stable collection name for this project.


def tokens(text: str) -> list[str]:
    """Lowercase tokenization; BM25 benefits from exact legal terms and numbers."""

    return re.findall(r"[a-z0-9]+(?:\\.[0-9]+)?", text.lower())  # Preserve terms like 0.5x as tokens.


class Retriever:
    """Own the dense index and sparse BM25 index behind one reusable interface."""

    def __init__(self, chunks: list[Chunk], qdrant_path: str = "./.qdrant_m4"):
        self.chunks = chunks  # Preserve the source records for citation rendering.
        self.client = QdrantClient(path=qdrant_path)  # Local persistent Qdrant; swap to URL/API key in deployment.
        self.bm25 = BM25Okapi([tokens(c.text) for c in chunks])  # Build sparse index from chunk text.
        self.embedder = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")  # Load reusable embedder.
        self._build_dense_index()  # Embed and store chunk vectors.

    def _build_dense_index(self) -> None:
        """Create a dense Qdrant collection and upsert corpus chunks."""

        if self.client.collection_exists(COLLECTION):
            self.client.delete_collection(COLLECTION)  # Rebuild to prevent stale chunks after corpus changes.
        self.client.create_collection(
            collection_name=COLLECTION,  # Target collection.
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),  # FastEmbed MiniLM vector size.
        )
        points = []  # Batch upsert points.
        for index, chunk in enumerate(self.chunks):
            vector = list(next(self.embedder.embed([chunk.text])))  # Embed source text with public FastEmbed API.
            points.append(PointStruct(
                id=index,  # Integer point IDs map back to self.chunks.
                vector=vector,  # Dense semantic representation.
                payload={"chunk_id": chunk.chunk_id, "document": chunk.document, "section": chunk.section},
            ))
        self.client.upsert(collection_name=COLLECTION, points=points)  # Persist dense points.

    def dense_search(self, query: str, limit: int) -> list[tuple[int, float]]:
        """Retrieve semantically similar chunks from Qdrant."""

        query_vector = list(next(self.embedder.query_embed(query)))  # Embed query with the model query interface.
        hits = self.client.query_points(
            collection_name=COLLECTION,  # Dense collection.
            query=query_vector,  # Embed the incoming user clause.
            limit=limit,  # Candidate count before later stages.
            with_payload=True,  # Retain provenance for debugging.
        ).points
        return [(int(hit.id), float(hit.score)) for hit in hits]  # Map Qdrant points back to chunk indexes.

    def sparse_search(self, query: str, limit: int) -> list[tuple[int, float]]:
        """Retrieve exact terms, clause labels, numbers, and defined legal phrases."""

        scores = self.bm25.get_scores(tokens(query))  # Score every corpus chunk with BM25.
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]  # Highest first.
        return [(index, float(scores[index])) for index in order if scores[index] > 0]  # Skip zero-overlap results.

    def _rrf(self, ranked_lists: list[list[tuple[int, float]]], k: int = 60) -> list[tuple[int, float]]:
        """Fuse dense and sparse rankings using Reciprocal Rank Fusion."""

        fused = defaultdict(float)  # Combined rank score by chunk index.
        for ranked in ranked_lists:
            for rank, (index, _score) in enumerate(ranked, start=1):
                fused[index] += 1.0 / (k + rank)  # RRF depends on rank, not incomparable raw scores.
        return sorted(fused.items(), key=lambda item: item[1], reverse=True)  # Best fused ranks first.

    def _rerank(self, query: str, candidates: list[tuple[int, float]]) -> list[tuple[int, float]]:
        """Simple transparent reranker; replace with a cross-encoder after baseline measurement."""

        query_terms = set(tokens(query))  # Terms present in the user's clause.
        rescored = []  # Keep candidate and reranking score.
        for index, original_score in candidates:
            chunk = self.chunks[index]  # Recover exact source passage.
            chunk_terms = set(tokens(chunk.text))  # Terms in candidate passage.
            overlap = len(query_terms & chunk_terms) / max(1, len(query_terms))  # Query-term coverage.
            authority_bonus = 0.02 * (5 - chunk.authority_rank)  # Prefer more authoritative source only as a small tie-break.
            rescored.append((index, overlap + authority_bonus + original_score * 0.01))  # Blend signals conservatively.
        return sorted(rescored, key=lambda item: item[1], reverse=True)  # Highest reranking score first.

    def search(self, query: str, top_k: int = 5, mode: str = "hybrid_rerank") -> list[tuple[Chunk, float]]:
        """Run one of the staged retrieval modes for controlled evaluation."""

        candidate_count = max(20, top_k * 4)  # Retrieve more candidates than the final answer needs.
        if mode == "dense":
            ranked = self.dense_search(query, candidate_count)  # Stage 1: dense baseline.
        elif mode == "hybrid":
            dense = self.dense_search(query, candidate_count)  # Stage 1: semantic retrieval.
            sparse = self.sparse_search(query, candidate_count)  # Stage 2: BM25 retrieval.
            ranked = self._rrf([dense, sparse])  # Stage 3: fuse rankings.
        elif mode == "hybrid_rerank":
            dense = self.dense_search(query, candidate_count)  # Semantic candidates.
            sparse = self.sparse_search(query, candidate_count)  # Lexical candidates.
            fused = self._rrf([dense, sparse])  # Combine complementary signals.
            ranked = self._rerank(query, fused[:candidate_count])  # Stage 4: rerank fused candidates.
        else:
            raise ValueError(f"Unsupported retrieval mode: {mode}")  # Reject accidental silent fallback.
        return [(self.chunks[index], score) for index, score in ranked[:top_k]]  # Return traceable top-k.
