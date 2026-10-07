# Import pytest for exception testing.
import pytest

# Import the output model.
from capstone.M1.models import ContractSummary

# Import the provenance validator.
from capstone.M1.validation import validate_provenance


# Test valid provenance.
def test_valid_provenance():

    # Create a summary whose raw text exists in the contract.
    summary = ContractSummary(

        # Contract ID.
        contract_id="CON-001",

        # Counterparty.
        counterparty="ABC",

        # Term clause.
        term={
            "raw_text": "The agreement shall commence on January 1, 2026."
        },

        # Other clauses are absent.
        termination={},
        liability_cap={},
        indemnification={},
        governing_law={},
    )

    # Original contract.
    contract_text = (
        "The agreement shall commence on January 1, 2026."
    )

    # This should not raise an exception.
    validate_provenance(
        summary,
        contract_text,
    )


# Test fabricated source text.
def test_invalid_provenance():

    # Create a summary with source text that does not exist.
    summary = ContractSummary(

        # Contract ID.
        contract_id="CON-002",

        # Counterparty.
        counterparty="XYZ",

        # This text is NOT present in the contract.
        term={
            "raw_text": "The contract automatically renews for five years."
        },

        # Other clauses are absent.
        termination={},
        liability_cap={},
        indemnification={},
        governing_law={},
    )

    # The original contract contains different text.
    contract_text = (
        "The agreement shall commence on January 1, 2026."
    )

    # The validator should reject the fabricated source.
    with pytest.raises(ValueError):

        # Run provenance validation.
        validate_provenance(
            summary,
            contract_text,
        )