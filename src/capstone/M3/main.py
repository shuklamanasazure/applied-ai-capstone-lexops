"""FastAPI entry point for LexOps M3."""

# Import FastAPI primitives.
from fastapi import FastAPI, HTTPException

# Import application service and request schemas.
from .schemas import IngestRequest, MemoryExtractRequest, NegotiationOutcome, SearchRequest
from .service import M3Service

# Create the FastAPI application.
app = FastAPI(title="LexOps M3", version="0.1.0")
# Create one reusable service object for all requests.
service = M3Service()


@app.get("/health")
def health() -> dict:
    # Provide a simple health endpoint for local testing.
    return {"status": "ok"}


@app.post("/m3/ingest")
def ingest(request: IngestRequest) -> dict:
    # Index the corpus into Qdrant.
    try:
        count = service.ingest(request.corpus_dir, request.recreate)
        # Return a compact result suitable for a demo.
        return {"status": "ok", "indexed_chunks": count}
    except Exception as exc:
        # Convert implementation errors into an HTTP 500 response.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/m3/search")
async def search(request: SearchRequest) -> dict:
    # Search both organizational knowledge and counterparty memory.
    try:
        results = await service.search(
            request.query,
            request.clause_type,
            request.counterparty_id,
            request.top_k,
        )
        # Return both sources so a future negotiation agent can reason over them.
        return {"query": request.query, "results": [item.model_dump() for item in results]}
    except Exception as exc:
        # Convert provider/database errors into a useful API response.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/m3/counterparties/{counterparty_id}/memory")
async def get_counterparty_memory(counterparty_id: str) -> dict:
    # Retrieve persistent memories for one counterparty.
    try:
        results = await service.get_memory(counterparty_id)
        # Return normalized memory records.
        return {"counterparty_id": counterparty_id, "memories": [item.model_dump() for item in results]}
    except Exception as exc:
        # Convert Supermemory failures into an HTTP error.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/m3/negotiations")
async def add_negotiation(request: NegotiationOutcome) -> dict:
    # Store a new historical negotiation outcome in Supermemory.
    try:
        memory_id = await service.add_negotiation(request)
        # Return the generated Supermemory identifier.
        return {"status": "stored", "memory_id": memory_id}
    except Exception as exc:
        # Convert external API failures into an HTTP error.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/m3/memory/extract")
async def extract_memory(request: MemoryExtractRequest) -> dict:
    # Build durable counterparty memories from stored negotiation evidence.
    try:
        result = await service.extract_memory(request.counterparty_id, request.query, request.top_k)
        # Return structured memories and their stored IDs.
        return result.model_dump()
    except Exception as exc:
        # Convert extraction/provider errors into an HTTP response.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
