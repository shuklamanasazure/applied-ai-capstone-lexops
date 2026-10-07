# Import the tool functions.
from .tools import (
    calculate_clause_risk,
    calculate_renewal_deadline,
)

# Import the memo writer.
from .memo_writer import write_review_memo

# Import the request and response models.
from .models import (
    MemoRequest,
    ReviewRequest,
    ReviewResponse,
)


# Define the tools that this agent is allowed to use.
ALLOWED_TOOLS = {
    "calculate_clause_risk",
    "calculate_renewal_deadline",
    "write_review_memo",
}


# Define actions that the agent must never perform.
FORBIDDEN_ACTIONS = {
    "approve_contract",
    "execute_contract",
    "send_legal_commitment",
    "represent_company_position",
}


# Run a contract review using the available tools.
def review_contract(request: ReviewRequest) -> ReviewResponse:

    # Keep track of the tools actually used.
    tools_used = []

    # Keep track of unauthorized actions.
    unauthorized_actions = []

    # -----------------------------------------
    # Step 1: Calculate clause risks
    # -----------------------------------------

    # Create an empty list for risk results.
    risk_results = []

    # Process every requested clause risk.
    for risk_request in request.risk_requests:

        # Call the deterministic risk calculator.
        result = calculate_clause_risk(risk_request)

        # Save the result.
        risk_results.append(result)

    # Record that the risk tool was used.
    if risk_results:

        tools_used.append("calculate_clause_risk")

    # -----------------------------------------
    # Step 2: Calculate renewal information
    # -----------------------------------------

    # Calculate the renewal deadline.
    renewal_result = calculate_renewal_deadline(
        request.renewal
    )

    # Record calendar tool usage.
    tools_used.append("calculate_renewal_deadline")

    # -----------------------------------------
    # Step 3: Create internal memo
    # -----------------------------------------

    # Build the memo request.
    memo_request = MemoRequest(
        contract=request.contract,
        risks=risk_results,
        renewal=renewal_result,
    )

    # Write the internal review memo.
    memo_result = write_review_memo(memo_request)

    # Record memo tool usage.
    tools_used.append("write_review_memo")

    # -----------------------------------------
    # Step 4: Enforce guardrails
    # -----------------------------------------

    # The agent is not given any implementation
    # for contract approval or execution.
    for action in FORBIDDEN_ACTIONS:

        # Confirm that the action was not executed.
        if action not in ALLOWED_TOOLS:

            # Record it as a prohibited capability.
            unauthorized_actions.append(action)

    # Return the complete review response.
    return ReviewResponse(
        risks=risk_results,
        renewal=renewal_result,
        memo=memo_result,
        tools_used=tools_used,
        unauthorized_actions=unauthorized_actions,
    )