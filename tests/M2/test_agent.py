# Import Decimal for financial values.
from decimal import Decimal

# Import the agent.
from capstone.M2.agent import review_contract

# Import the request models.
from capstone.M2.models import (
    ContractSummary,
    RenewalRequest,
    ReviewRequest,
    RiskRequest,
)


# Test the complete single-agent workflow.
def test_agent_review_contract():

    # Create the contract summary.
    contract = ContractSummary(
        contract_id="C-100",
        counterparty="ABC Corp",
        contract_value=Decimal("2000000"),
        description="Technology services agreement",
    )

    # Create a risk calculation request.
    risk_request = RiskRequest(
        clause_type="liability_cap",
        contract_value=Decimal("2000000"),
        contract_position=Decimal("500000"),
        playbook_position=Decimal("1000000"),
    )

    # Create the renewal request.
    renewal_request = RenewalRequest(
        contract_id="C-100",
        renewal_date="2027-12-31",
        notice_period=60,
    )

    # Build the agent request.
    request = ReviewRequest(
        contract=contract,
        risk_requests=[risk_request],
        renewal=renewal_request,
    )

    # Run the single agent.
    result = review_contract(request)

    # Verify that the risk tool was called.
    assert "calculate_clause_risk" in result.tools_used

    # Verify that the calendar tool was called.
    assert "calculate_renewal_deadline" in result.tools_used

    # Verify that the memo tool was called.
    assert "write_review_memo" in result.tools_used

    # Verify that the risk calculation was correct.
    assert result.risks[0].deviation == -50.0

    # Verify the renewal calculation.
    assert result.renewal.notice_deadline == "2027-11-01"

    # Verify that the memo was created.
    assert result.memo.file_path.endswith(
        "C-100_review.md"
    )

    # Verify that the agent did not approve the contract.
    assert "approve_contract" in result.unauthorized_actions

    # Verify that the agent did not execute the contract.
    assert "execute_contract" in result.unauthorized_actions

# This is particularly important because your assignment explicitly asks:
# Did it call the correct tool?
# Did it call unnecessary tools?
# Were tool arguments correct?
# Did it attempt an unauthorized action?

# Run everything via command uv run pytest tests/M2 