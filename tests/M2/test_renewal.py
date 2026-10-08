# Import the renewal tool.
from capstone.M2.tools import calculate_renewal_deadline

# Import the request model.
from capstone.M2.models import RenewalRequest


# Test renewal deadline calculation.
def test_renewal_deadline():

    # Create the renewal request.
    request = RenewalRequest(
        contract_id="C-100",
        renewal_date="2027-12-31",
        notice_period=60,
    )

    # Calculate the renewal event.
    result = calculate_renewal_deadline(request)

    # Verify the renewal date.
    assert result.renewal_date == "2027-12-31"

    # Verify the calculated notice deadline.
    assert result.notice_deadline == "2027-11-01"

    # Verify the urgency.
    assert result.urgency == "NORMAL"