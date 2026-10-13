"""Pydantic v2 request/response contracts for the M4 API."""

from typing import Literal  # Constrain evaluation labels to approved values.
from pydantic import BaseModel, Field  # Validate API inputs and outputs.


class SearchRequest(BaseModel):
    """The clause or question to compare with the playbook."""

    query: str = Field(min_length=5, max_length=5000)  # Reject empty or excessive queries.
    top_k: int = Field(default=5, ge=1, le=20)  # Bound retrieval cost.
    mode: Literal["dense", "hybrid", "hybrid_rerank"] = "hybrid_rerank"  # Allow staged comparisons.


class Citation(BaseModel):
    """Traceable source metadata attached to each retrieved chunk."""

    source_document: str  # Original file name.
    source_section: str  # Heading or best available section label.
    source_chunk: str  # Stable chunk identifier.
    source_text: str  # Exact text retrieved from the source.
    authority_rank: int  # Lower numbers mean more authoritative sources.
    score: float  # Final ranking score.


class GroundedAnswer(BaseModel):
    """A conservative answer whose claims are traceable to source text."""

    recommendation: str  # Short interpretation based on retrieved text.
    citations: list[Citation]  # Exact source evidence supporting the recommendation.
    groundedness: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED"]  # Evaluation result.
    groundedness_reason: str  # Explain the deterministic evaluation result.
    disclaimer: str = "For workflow support only; legal review is required."  # Avoid implying legal advice.


class SearchResponse(BaseModel):
    """API response with both retrieval results and grounded answer."""

    query: str  # Original request.
    mode: str  # Retrieval stage used.
    results: list[Citation]  # Ranked evidence.
    answer: GroundedAnswer  # Source-grounded interpretation.
