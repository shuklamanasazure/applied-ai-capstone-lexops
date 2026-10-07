# Import Decimal for accurate financial calculations.
from decimal import Decimal

# Import date and timedelta for calendar calculations.
from datetime import date, timedelta

# Import the Pydantic models used by the tools.
from .models import RiskRequest, RiskResult

# Import the renewal models.
from .models import RenewalRequest, RenewalEvent


# Calculate risk based on deviation from the internal playbook.
def calculate_clause_risk(request: RiskRequest) -> RiskResult:

    # Read the playbook position.
    playbook = request.playbook_position

    # Prevent division by zero.
    if playbook == 0:

        # Return a clear error to the caller.
        raise ValueError("Playbook position cannot be zero.")

    # Calculate percentage deviation from the playbook.
    deviation = (
        (request.contract_position - playbook)
        / playbook
        * Decimal("100")
    )

    # Convert the deviation to a positive risk score.
    # Based on data given risk s core can be taken from ./data/lexops/mock_api/contracts.json risk_score
    risk_score = min(abs(float(deviation)), 100.0)

    # Assign a risk level based on the deviation.
    if risk_score < 10:

        # Small deviation.
        risk_level = "LOW"

    elif risk_score < 25:

        # Moderate deviation.
        risk_level = "MEDIUM"

    elif risk_score < 50:

        # Significant deviation.
        risk_level = "HIGH"

    else:

        # Very significant deviation.
        risk_level = "CRITICAL"

    # Create a simple explanation for the reviewer.
    explanation = (
        f"{request.clause_type} deviates by "
        f"{float(deviation):.1f}% from the playbook position."
    )

    # Return the strongly typed result.
    return RiskResult(
        clause_type=request.clause_type,
        risk_score=round(risk_score, 2),
        risk_level=risk_level,
        deviation=round(float(deviation), 2),
        explanation=explanation,
    )


# Calculate the renewal notice deadline.
def calculate_renewal_deadline(
    request: RenewalRequest,
) -> RenewalEvent:

    # Convert the input renewal date into a Python date.
    renewal_date = date.fromisoformat(request.renewal_date)

    # Subtract the required notice period.
    notice_deadline = (
        renewal_date
        - timedelta(days=request.notice_period)
    )

    # For M2, classify the event using the notice period.
    if request.notice_period <= 15:

        # Short notice period.
        urgency = "CRITICAL"

    elif request.notice_period <= 30:

        # Medium notice period.
        urgency = "URGENT"

    else:

        # Sufficient notice period.
        urgency = "NORMAL"

    # Return the calculated renewal event.
    return RenewalEvent(
        contract_id=request.contract_id,
        renewal_date=renewal_date.isoformat(),
        notice_deadline=notice_deadline.isoformat(),
        urgency=urgency,
    )

