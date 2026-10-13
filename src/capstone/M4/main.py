"""FastAPI application entry point for the LexOps M4 RAG pipeline."""

import os  # Read environment-based configuration.
from pathlib import Path  # Work with corpus paths.
from dotenv import load_dotenv  # Load environment variables from .env file.
from fastapi import FastAPI, HTTPException  # HTTP API and client error handling.
from capstone.M4.corpus import load_corpus  # Corpus ingestion.
from capstone.M4.retrieval import Retriever  # Dense, sparse, fusion, and reranking.
from capstone.M4.schemas import SearchRequest, SearchResponse  # Pydantic v2 contracts.
from .grounding import build_answer  # Recommendation and groundedness evaluation.

# Load environment variables from .env in the current working directory.
load_dotenv()


CORPUS_DIR = Path(os.getenv("LEXOPS_CORPUS_DIR", "./data/lexops/corpus"))  # Use assignment corpus path.
QDRANT_PATH = os.getenv("LEXOPS_QDRANT_PATH", "./.qdrant_m4")  # Persist local Qdrant data.
MIN_CHUNK_CHARS = int(os.getenv("LEXOPS_MIN_CHUNK_CHARS", "40"))  # Tune ingestion noise threshold.
retriever = None  # Initialize lazily so importing the module does not load embeddings during tests.

app = FastAPI(title="LexOps M4 Grounded RAG", version="0.1.0")  # Create documented API.


@app.on_event("startup")
def startup() -> None:
    """Load source documents and build retrieval indexes once at service startup."""

    global retriever  # Share the initialized retriever across requests.
    chunks = load_corpus(CORPUS_DIR, min_chunk_chars=MIN_CHUNK_CHARS)  # Parse the local corpus.
    retriever = Retriever(chunks, qdrant_path=QDRANT_PATH)  # Build dense and sparse indexes.


@app.get("/health")
def health() -> dict:
    """Expose a minimal readiness signal."""

    return {"status": "ok", "index_loaded": retriever is not None}  # Keep health response lightweight.


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    """Retrieve playbook evidence and return a grounded recommendation with citations."""

    if retriever is None:
        raise HTTPException(status_code=503, detail="Search index is not ready.")  # Avoid misleading empty results.
    try:
        ranked = retriever.search(request.query, top_k=request.top_k, mode=request.mode)  # Run selected stage.
        answer = build_answer(request.query, ranked)  # Build answer and evaluate citations.
        return SearchResponse(
            query=request.query,  # Echo user clause.
            mode=request.mode,  # Report measured retrieval mode.
            results=answer["citations"],  # Return ranked evidence.
            answer=answer,  # Include recommendation and groundedness label.
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc  # Return actionable request error.
