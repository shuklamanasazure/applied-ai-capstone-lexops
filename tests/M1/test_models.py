# Import pytest for testing.
import pytest

# Import the models that we want to test.
from capstone.M1.models import (
    ContractReviewRequest,
    ContractSummary,
)


# Test that a valid request can be created.
def test_contract_review_request():

    # Create a valid request.
    request = ContractReviewRequest(
        contract_id="CON-001",
        counterparty="ABC Corp",
        contract_text="The agreement starts on January 1, 2026.",
    )

    # Verify that the ID was stored correctly.
    assert request.contract_id == "CON-001"


# Test that the output model accepts valid data.
def test_contract_summary():

    # Create a valid ContractSummary.
    summary = ContractSummary(

        # Contract identifier.
        contract_id="CON-001",

        # Counterparty.
        counterparty="ABC Corp",

        # Term clause.
        term={
            "raw_text": "The term shall commence on January 1, 2026.",
            "start_date": "2026-01-01",
            "end_date": None,
            "renewal": None,
        },

        # Termination clause.
        termination={
            "raw_text": "Either party may terminate with 30 days notice.",
            "notice_period": "30 days",
            "termination_rights": "Either party may terminate.",
        },

        # Liability clause.
        liability_cap={
            "raw_text": "Liability shall not exceed $1 million.",
            "amount": 1000000,
            "multiplier": None,
            "exceptions": None,
        },

        # Indemnification clause.
        indemnification={
            "raw_text": "Vendor shall indemnify Customer against third-party claims.",
            "scope": "Third-party claims.",
        },

        # Governing law.
        governing_law={
            "raw_text": "This agreement shall be governed by the laws of Delaware.",
            "jurisdiction": "Delaware",
        },
    )

    # Verify that Pydantic converted the date correctly.
    assert summary.term.start_date.year == 2026

    # Verify the liability amount.
    assert summary.liability_cap.amount == 1000000

    # Verify the jurisdiction.
    assert summary.governing_law.jurisdiction == "Delaware"

# Test that a missing clause can be represented with null.
def test_missing_clause():

    # Create a summary where termination was not found.
    summary = ContractSummary(

        # Contract identifier.
        contract_id="CON-002",

        # Counterparty.
        counterparty="XYZ Corp",

        # Term exists.
        term={},

        # Termination does not exist.
        termination={
            "raw_text": None,
            "notice_period": None,
            "termination_rights": None,
        },

        # Liability exists.
        liability_cap={},

        # Indemnification exists.
        indemnification={},

        # Governing law exists.
        governing_law={},
    )

    # Verify that the system represents absence as null.
    assert summary.termination.raw_text is None