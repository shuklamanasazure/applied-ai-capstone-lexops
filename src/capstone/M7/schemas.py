from typing import Literal  # Restrict values to explicit choices.
from pydantic import BaseModel, Field  # Validate request and output data.


class ReviewRequest(BaseModel):
    review_id: str = Field(min_length=1)  # Stable ID used to correlate logs and traces.
    contract_id: str = Field(min_length=1)  # Internal contract identifier; avoid contract text here.
    counterparty: str = Field(min_length=1, max_length=120)  # Keep metadata short and non-sensitive.
    document_text: str = Field(min_length=1, repr=False)  # Input content is hidden from repr by default.


class ReviewResult(BaseModel):
    review_id: str  # Links the result to the originating request.
    contract_id: str  # Internal contract identifier.
    risk_score: int = Field(ge=0, le=100)  # Risk score must be between 0 and 100.
    latency_ms: int = Field(ge=0)  # End-to-end workflow latency in milliseconds.
    final_route: Literal["auto_approve", "human_review"]  # Only allow known routes.
    human_decision: Literal["pending", "approved", "rejected"]  # Never invent a human decision.
    model: str  # Model label configured for this run.
    prompt_version: str  # Version of the extraction/review prompt.
    token_usage: dict[str, int] = Field(default_factory=dict)  # Empty for the mock implementation.
    retrieval_results: list[str] = Field(default_factory=list)  # Use IDs, not full document text.
    tool_calls: list[str] = Field(default_factory=list)  # Names of tools called during this run.
    errors: list[str] = Field(default_factory=list)  # Sanitized error codes/messages only.
