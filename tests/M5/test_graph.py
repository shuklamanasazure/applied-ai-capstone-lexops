# Import the nodes being tested.
from capstone.m5.nodes import compare_node, risk_node


# Test that matching contract clauses receive zero risk.
def test_matching_clause_has_zero_risk():
    # Construct a state with one clause matching the playbook.
    state = {
        "contract_summary": {
            "counterparty": "Northwind",
            "clauses": [
                {
                    "clause_type": "liability",
                    "contract_text": "Liability is capped at fees paid in the previous 12 months.",
                    "standard_text": "Liability is capped at fees paid in the previous 12 months.",
                    "risk_score": 0,
                    "deviation": "",
                }
            ],
        },
        "audit_events": [],
    }

    # Run the comparison node.
    result = compare_node(state)

    # Verify that matching wording has no deviation risk.
    assert result["playbook_results"]["risk_score"] == 0


# Test that the risk policy flags a non-standard contract.
def test_non_standard_contract_requires_approval():
    # Create a comparison result with a high risk score.
    state = {
        "playbook_results": {
            "risk_score": 80,
            "clauses": [],
            "rationale": ["Liability cap differs"],
        },
        "audit_events": [],
    }

    # Apply the deterministic risk policy.
    result = risk_node(state)

    # Verify the classification and approval requirement.
    assert result["risk_level"] == "non_standard"
    assert result["approval_required"] is True


# Test the exact policy boundary.
def test_risk_score_70_requires_approval():
    # Construct a state at the configured risk threshold.
    state = {
        "playbook_results": {"risk_score": 70},
        "audit_events": [],
    }

    # Assess the risk.
    result = risk_node(state)

    # Confirm that 70 belongs to the human-review path.
    assert result["risk_level"] == "non_standard"
    assert result["approval_required"] is True