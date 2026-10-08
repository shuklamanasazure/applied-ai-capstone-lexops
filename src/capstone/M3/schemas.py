"""Pydantic v2 request and response contracts for M3."""

# Import Pydantic model and field helpers.
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    # Allow a custom corpus path while defaulting to configured corpus.
    corpus_dir: str | None = None
    # Rebuild the collection when true; useful during demos.
    recreate: bool = False


class SearchRequest(BaseModel):
    # Natural-language negotiation question.
    query: str = Field(min_length=3)
    # Optional clause type filter such as liability or termination.
    clause_type: str | None = None
    # Optional counterparty filter for precedent search.
    counterparty_id: str | None = None
    # Number of Qdrant and memory results requested.
    top_k: int = Field(default=5, ge=1, le=20)


class NegotiationOutcome(BaseModel):
    # Stable counterparty identifier.
    counterparty_id: str
    # Contract identifier from the historical negotiation.
    contract_id: str
    # Clause being negotiated.
    clause_type: str
    # What the counterparty requested.
    request: str
    # What the firm finally approved or proposed.
    outcome: str
    # Optional business/legal rationale.
    rationale: str | None = None
    # Optional source filename for traceability.
    source: str | None = None


class MemoryExtractRequest(BaseModel):
    # Counterparty whose historical behavior should be summarized.
    counterparty_id: str
    # Query used to retrieve relevant memories before extraction.
    query: str = "negotiation preferences accepted rejected terms recurring positions"
    # Number of memories used as extraction context.
    top_k: int = Field(default=10, ge=1, le=20)


class MemoryItem(BaseModel):
    # A concise durable statement about counterparty behavior.
    statement: str
    # Type makes the memory easier for an agent to reason over.
    memory_type: str
    # Evidence from a historical negotiation.
    evidence: str


class MemoryExtractResponse(BaseModel):
    # Counterparty associated with the extracted memory.
    counterparty_id: str
    # Structured durable memories.
    memories: list[MemoryItem]
    # Supermemory document IDs created for those memories.
    stored_ids: list[str]


class SearchResult(BaseModel):
    # Source system: qdrant or supermemory.
    source: str
    # Similarity/relevance score when available.
    score: float | None = None
    # Human-readable content.
    content: str
    # Metadata such as clause type and source file.
    metadata: dict = Field(default_factory=dict)
