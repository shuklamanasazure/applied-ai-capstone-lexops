
# src/capstone/M6/schemas.py

from typing import Literal, TypedDict  # Define constrained values and graph state.
from pydantic import BaseModel, Field  # Validate agent inputs and outputs.


class Clause(BaseModel):
    # Store one normalized clause extracted from the contract.
    name: str
    text: str
    section: str = "unknown"


class ContractSummary(BaseModel):
    # Store extraction results only; do not add a risk score here.
    contract_id: str
    counterparty_id: str
    clauses: list[Clause] = Field(default_factory=list)


class PlaybookFinding(BaseModel):
    # Describe a comparison against an authoritative playbook entry.
    clause_name: str
    standard_text: str
    fallback_text: str
    source: str
    deviation: bool


class RedlineProposal(BaseModel):
    # Store proposed wording separately from the review decision.
    clause_name: str
    original_text: str
    proposed_text: str
    explanation: str
    approved_fallback: str


class LegalDecision(BaseModel):
    # Only the legal reviewer assigns the review status.
    status: Literal[
        "auto_approve", "human_review", "rejected"
    ]
    reasons: list[str] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    # Validate the API request.
    contract_id: str = Field(min_length=1)


class ReviewState(TypedDict, total=False):
    # Pass data between LangGraph nodes using a shared state.
    contract_id: str
    contract_text: str
    counterparty_id: str
    summary: dict
    findings: list[dict]
    redlines: list[dict]
    decision: dict
    error: str

    # Logic: ContractSummary contains normalized clauses but no risk classification. PlaybookFinding contains the comparison evidence, 
    # while RedlineProposal contains only proposed changes. LegalDecision is owned by the reviewer.