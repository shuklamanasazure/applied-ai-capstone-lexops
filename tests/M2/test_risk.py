# Import Decimal for exact monetary test values.
from decimal import Decimal

# Import the risk tool.
from capstone.M2.tools import calculate_clause_risk

# Import the request model.
from capstone.M2.models import RiskRequest


# Test a 50% deviation from the playbook.
def test_liability_cap_risk():

    # Create the input for the risk calculator.
    request = RiskRequest(
        clause_type="liability_cap",
        contract_value=Decimal("2000000"),
        contract_position=Decimal("500000"),
        playbook_position=Decimal("1000000"),
    )

    # Execute the deterministic tool.
    result = calculate_clause_risk(request)

    # Verify the deviation.
    assert result.deviation == -50.0

    # Verify the risk score.
    assert result.risk_score == 50.0

    # Verify the risk level.
    assert result.risk_level == "CRITICAL"

    # To run this test, use the following command in the terminal:
    # uv run pytest tests/M2/test_risk.py