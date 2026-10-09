# Import the shared workflow state type.
from typing import Any

# Import the structured models.
from capstone.M5.schemas import ContractClause, ContractSummary, ReviewState



# Extract a clause when a known heading appears in the contract.
def extract_node(state: dict[str, Any]) -> dict[str, Any]:
    # Read the contract text from the current graph state.
    contract = state["contract"]

    # Read the counterparty name.
    counterparty = state["counterparty"]

    # Define the supported clause types and their standard wording.
    standards = {
        "liability": "Liability is capped at fees paid in the previous 12 months.",
        "termination": "Either party may terminate with 30 days notice.",
        "indemnity": "Indemnification is limited to third-party claims.",
    }

    # Start with an empty list of extracted clauses.
    clauses = []

    # Inspect every clause type configured above.
    for clause_type, standard_text in standards.items():
        # Use the standard text as a mock contract clause if no heading is found.
        contract_text = standard_text

        # Look for a simple clause heading in the contract.
        for line in contract.splitlines():
            # Match a heading such as "liability: unlimited".
            if line.lower().startswith(f"{clause_type}:"):
                # Keep the text following the heading.
                contract_text = line.split(":", 1)[1].strip()
                # Stop searching once the heading is found.
                break

        # Create a validated clause record.
        clauses.append(
            ContractClause(
                clause_type=clause_type,
                contract_text=contract_text,
                standard_text=standard_text,
            )
        )

    # Validate the complete extraction output.
    summary = ContractSummary(
        counterparty=counterparty,
        clauses=clauses,
    )

    # Return only the fields updated by this node.
    return {
        "contract_summary": summary.model_dump(),
        "audit_events": state.get("audit_events", []) + ["clauses_extracted"],
    }


# Compare the extracted clauses with the approved playbook.
def compare_node(state: dict[str, Any]) -> dict[str, Any]:
    # Read the extracted summary from the state.
    summary = ContractSummary.model_validate(state["contract_summary"])

    # Prepare the list of clauses after comparison.
    compared_clauses = []

    # Keep a list of explanations for the reviewer.
    rationale = []

    # Compare each clause with its standard.
    for clause in summary.clauses:
        # Normalize whitespace and case for this basic comparison.
        actual = " ".join(clause.contract_text.lower().split())
        standard = " ".join(clause.standard_text.lower().split())

        # Assign zero risk when wording matches the configured standard.
        if actual == standard:
            risk_score = 0
            deviation = "Matches the approved standard."
        else:
            # Flag differences for risk assessment.
            risk_score = 80
            deviation = "Contract wording differs from the approved standard."

        # Store the comparison results in a new validated clause.
        compared_clauses.append(
            clause.model_copy(
                update={
                    "risk_score": risk_score,
                    "deviation": deviation,
                }
            )
        )

        # Record only clauses that differ from the standard.
        if risk_score > 0:
            rationale.append(f"{clause.clause_type}: {deviation}")

    # Use the highest clause risk as the overall risk score.
    overall_risk = max(
        (clause.risk_score for clause in compared_clauses),
        default=0,
    )

    # Return the structured comparison and audit event.
    return {
        "playbook_results": {
            "clauses": [
                clause.model_dump() for clause in compared_clauses
            ],
            "risk_score": overall_risk,
            "rationale": rationale,
        },
        "audit_events": state.get("audit_events", []) + ["playbook_compared"],
    }


# Apply deterministic policy rather than asking an LLM to choose the route.
def risk_node(state: dict[str, Any]) -> dict[str, Any]:
    # Read the risk score calculated by the comparison node.
    risk_score = state["playbook_results"]["risk_score"]

    # Use the example policy threshold of 70.
    risk_level = "non_standard" if risk_score >= 70 else "standard"

    # Mark high-risk contracts for human approval.
    approval_required = risk_score >= 70

    # Return the decision inputs used by conditional routing.
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "approval_required": approval_required,
        "audit_events": state.get("audit_events", []) + [
            f"risk_assessed:{risk_level}:{risk_score}"
        ],
    }


# Draft redlines for non-standard clauses.
def draft_redline_node(state: dict[str, Any]) -> dict[str, Any]:
    # Read the clauses identified during comparison.
    clauses = state["playbook_results"]["clauses"]

    # Create a proposed change for each clause with a deviation.
    changes = [
        f"{clause['clause_type']}: propose '{clause['standard_text']}' "
        f"in place of '{clause['contract_text']}'."
        for clause in clauses
        if clause["risk_score"] > 0
    ]

    # Store the proposed redlines without approving them.
    return {
        "redline": changes,
        "audit_events": state.get("audit_events", []) + ["redline_drafted"],
    }


# Prepare the review package for the standard path.
def prepare_standard_node(state: dict[str, Any]) -> dict[str, Any]:
    # No amendment is needed when every clause matches the standard.
    return {
        "redline": [],
        "decision": "auto_approved",
        "audit_events": state.get("audit_events", []) + [
            "standard_path_prepared"
        ],
    }


# Pause the workflow and request a human decision.
def human_review_node(state: dict[str, Any]) -> dict[str, Any]:
    # Import interrupt locally to make its role explicit.
    from langgraph.types import interrupt

    # Send the reviewer a structured approval request.
    response = interrupt(
        {
            "review_id": state["review_id"],
            "counterparty": state["counterparty"],
            "risk_score": state["risk_score"],
            "risk_level": state["risk_level"],
            "redline": state.get("redline", []),
            "question": "Approve or reject these proposed contract redlines?",
        }
    )

    # Validate the decision received when the graph resumes.
    from capstone.M5.schemas import ApprovalRequest

    # Reject malformed decisions before they enter the final state.
    approval = ApprovalRequest.model_validate(response)

    # Map the reviewer's decision to an explicit workflow outcome.
    decision = (
        "human_approved"
        if approval.decision == "approve"
        else "human_rejected"
    )

    # Record who made the decision and why.
    event = (
        f"human_decision:{approval.decision}:"
        f"reviewer={approval.reviewer}:comment={approval.comment}"
    )

    # Return the validated decision and its audit event.
    return {
        "human_decision": approval.decision,
        "reviewer": approval.reviewer,
        "decision": decision,
        "audit_events": state.get("audit_events", []) + [event],
    }


# Assemble the final internal review package.
def finalize_node(state: dict[str, Any]) -> dict[str, Any]:

    # Temporary diagnostic: inspect keys available at finalization.
    print("DEBUG finalize_node keys:", list(state.keys()))
    print("DEBUG review_id:", state.get("review_id"))
    
    # Add the finalization event to the audit trail.
    events = state.get("audit_events", []) + ["review_finalized"]

    # Construct the final review package from workflow state.
    from capstone.M5.schemas import ReviewPackage

    # Validate that the final output contains the expected fields.
    package = ReviewPackage(
        review_id=state["review_id"],
        counterparty=state["counterparty"],
        risk_score=state["risk_score"],
        risk_level=state["risk_level"],
        redline=state.get("redline", []),
        decision=state.get("decision", "pending"),
        approval_required=state["approval_required"],
        reviewer=state.get("reviewer"),
        audit_events=events,
    )

    # Return a JSON-compatible package to the caller.
    return {
        "review_package": package.model_dump(),
        "audit_events": events,
    }