"""Small unit tests that do not require external APIs."""

# Import pytest for assertions.
import pytest

# Import the Pydantic request contract.
from app.schemas import SearchRequest, NegotiationOutcome


def test_search_request_defaults_top_k():
    # Validate that the API contract supplies the expected default.
    request = SearchRequest(query="liability cap")
    # The default should be five results.
    assert request.top_k == 5


def test_search_request_rejects_short_query():
    # Confirm the minimum query length is enforced by Pydantic v2.
    with pytest.raises(Exception):
        SearchRequest(query="x")


def test_negotiation_outcome_contract():
    # Create a valid historical negotiation outcome.
    outcome = NegotiationOutcome(
        counterparty_id="acme",
        contract_id="acme-2026",
        clause_type="liability",
        request="5x annual fees",
        outcome="approved 2x annual fees",
    )
    # Confirm the key fields are retained.
    assert outcome.counterparty_id == "acme"
    assert outcome.clause_type == "liability"
