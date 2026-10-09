# Import Literal to restrict values to an approved set.
from typing import Literal

# Import Pydantic v2 model and field validation.
from pydantic import BaseModel, Field, ConfigDict

# Import TypedDict for a documented graph-state contract.
from typing import TypedDict, Any


# Represent one extracted contract clause.
class ContractClause(BaseModel):
    # Reject unknown fields to catch mistakes early.
    model_config = ConfigDict(extra="forbid")

    # Identify the clause, such as liability_cap or termination.
    clause_type: str

    # Store the actual wording found in the contract.
    contract_text: str

    # Store the approved wording from the firm's playbook.
    standard_text: str = ""

    # Store the deviation risk assigned to this clause.
    risk_score: int = Field(default=0, ge=0, le=100)

    # Explain why the wording differs from the standard.
    deviation: str = ""


# Represent the extraction result.
class ContractSummary(BaseModel):
    # Store the counterparty name.
    counterparty: str

    # Store the extracted clauses.
    clauses: list[ContractClause] = Field(default_factory=list)


# Represent the result of playbook comparison.
class ClauseComparison(BaseModel):
    # Store each clause with its comparison results.
    clauses: list[ContractClause] = Field(default_factory=list)

    # Store the aggregate risk score from 0 to 100.
    risk_score: int = Field(ge=0, le=100)

    # Explain the main risks for the reviewer.
    rationale: list[str] = Field(default_factory=list)


# Represent the proposed redline package.
class RedlineDraft(BaseModel):
    # Store the proposed clause-level amendments.
    proposed_changes: list[str] = Field(default_factory=list)

    # State whether a lawyer must review the proposal.
    approval_required: bool


# Represent the decision submitted by a human reviewer.
class ApprovalRequest(BaseModel):
    # Accept only an explicit approve or reject decision.
    decision: Literal["approve", "reject"]

    # Capture the reviewer's identity for the audit record.
    reviewer: str = Field(min_length=1)

    # Capture the reason or review comments.
    comment: str = ""


# Validate the incoming API request.
class ReviewRequest(BaseModel):
    # Identify the contract review.
    review_id: str = Field(min_length=1)

    # Store the counterparty.
    counterparty: str = Field(min_length=1)

    # Store the complete contract text.
    contract: str = Field(min_length=1)


# Represent the final internal review package.
class ReviewPackage(BaseModel):
    # Identify the review.
    review_id: str

    # Identify the counterparty.
    counterparty: str

    # Store the final risk score.
    risk_score: int

    # Store the standard or non-standard classification.
    risk_level: Literal["standard", "non_standard"]

    # Store the proposed redline changes.
    redline: list[str]

    # Store the final workflow outcome.
    decision: str

    # Explain whether human approval was required.
    approval_required: bool

    # Record the human reviewer when applicable.
    reviewer: str | None = None

    # Store a chronological audit trail.
    audit_events: list[str] = Field(default_factory=list)

# Define every field that the workflow can read or update.
class ReviewState(TypedDict, total=False):
    # Stable identifiers for checkpointing and audit.
    review_id: str
    counterparty: str
    contract: str

    # Structured intermediate results.
    contract_summary: dict[str, Any]
    playbook_results: dict[str, Any]
    risk_score: int
    risk_level: str

    # Routing, redline, and approval fields.
    approval_required: bool
    redline: list[str]
    human_decision: str
    reviewer: str
    decision: str

    # Audit and final output.
    audit_events: list[str]
    review_package: dict[str, Any]