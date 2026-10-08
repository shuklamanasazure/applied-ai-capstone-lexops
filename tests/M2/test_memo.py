# Import Decimal for contract value.
from decimal import Decimal

# Import the memo writer.
from capstone.M2.memo_writer import write_review_memo

# Import all required models.
from capstone.M2.models import (
    ContractSummary,
    MemoRequest,
    RenewalEvent,
    RiskResult,
)


# Test that a memo is actually written to disk.
def test_write_review_memo(tmp_path):

    # Create a sample contract summary.
    contract = ContractSummary(
        contract_id="C-100",
        counterparty="ABC Corp",
        contract_value=Decimal("1000000"),
        description="Technology services agreement",
    )

    # Create a sample risk result.
    risk = RiskResult(
        clause_type="liability_cap",
        risk_score=50,
        risk_level="CRITICAL",
        deviation=-50,
        explanation="50% below playbook.",
    )

    # Create a sample renewal result.
    renewal = RenewalEvent(
        contract_id="C-100",
        renewal_date="2027-12-31",
        notice_deadline="2027-11-01",
        urgency="NORMAL",
    )

    # Create the memo request.
    request = MemoRequest(
        contract=contract,
        risks=[risk],
        renewal=renewal,
    )

    # Write the memo into pytest's temporary directory.
    result = write_review_memo(
        request,
        output_directory=str(tmp_path),
    )

    # Verify that the file exists.
    assert tmp_path.joinpath(
        "C-100_review.md"
    ).exists()

    # Verify that important content exists.
    assert "CRITICAL" in result.content

    # Verify that the contract ID exists.
    assert "C-100" in result.content