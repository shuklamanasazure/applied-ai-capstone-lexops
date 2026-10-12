from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class AgentAnswer(BaseModel):
    """Structured candidate answer returned by the upstream LexOps agent."""
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high", "critical"]
    proposed_route: Literal["auto_approve", "human_review", "reject"]

class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1)
    retrieved_documents: list[str] = Field(default_factory=list)
    # For harness testing, supply the output of your existing M1-M7 agent here.
    candidate: AgentAnswer
    # Optional IDs of retrieved sources; citations must match these IDs.
    source_ids: list[str] = Field(default_factory=list)

class JudgeResult(BaseModel):
    judge: str
    score: float = Field(ge=0.0, le=1.0)
    faithful: bool
    reason: str = ""

class ReviewResponse(BaseModel):
    answer: str
    citations: list[str]
    risk_score: float
    final_route: Literal["auto_approve", "human_review", "reject"]
    disclaimer: str = "Not legal advice. Human review required."
    guardrail_flags: list[str] = Field(default_factory=list)
    judge_scores: dict[str, float | None] = Field(default_factory=dict)
    judge_consensus: Literal["agree_faithful", "disagree", "not_evaluated"] = "not_evaluated"
