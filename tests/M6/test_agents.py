
# tests/M6/test_agents.py

import os  # Read test configuration.
import pytest  # Provide test fixtures and assertions.

from capstone.M6.repository import ContractRepository
from capstone.M6.agents import ExtractionAgent, LegalReviewer
from capstone.M6.schemas import ContractSummary, PlaybookFinding


@pytest.fixture
def contract_id():
    # Supply a real ID from the local mock repository.
    value = os.getenv("LEXOPS_TEST_CONTRACT_ID")
    if not value:
        pytest.skip("Set LEXOPS_TEST_CONTRACT_ID to a fixture ID.")
    return value


def test_extraction_returns_summary(contract_id):
    # Construct the extraction agent with the repository adapter.
    agent = ExtractionAgent(ContractRepository())

    # Extract clauses from the selected fixture.
    summary = agent.run(contract_id)

    # Verify the typed contract and its identity.
    assert isinstance(summary, ContractSummary)
    assert summary.contract_id == contract_id

    # Verify that extraction has no risk field.
    assert "risk" not in summary.model_dump()


def test_missing_playbook_requires_human_review():
    # Build an empty but valid summary.
    summary = ContractSummary(
        contract_id="TEST-1",
        counterparty_id="VENDOR-1",
        clauses=[],
    )

    # Model missing authoritative evidence.
    finding = PlaybookFinding(
        clause_name="unknown",
        standard_text="No standard found",
        fallback_text="",
        source="not-found",
        deviation=True,
    )

    # Invoke the legal reviewer with incomplete evidence.
    decision = LegalReviewer().run(summary, [finding], [])

    # Verify that the workflow requests human review.
    assert decision.status == "human_review"




# # Execute the M6 test suite.
# PYTHONPATH=src uv run pytest tests/M6 -v

# # Run the extraction test against an actual fixture.
# LEXOPS_TEST_CONTRACT_ID="YOUR-REAL-CONTRACT-ID" \
#   PYTHONPATH=src uv run pytest tests/M6/test_agents.py -v