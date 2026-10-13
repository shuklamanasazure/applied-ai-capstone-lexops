"""Unit tests for source-groundedness evaluation."""

from lexops_m4.corpus import Chunk  # Construct test evidence.
from lexops_m4.grounding import evaluate_groundedness  # Test deterministic evaluator.


def test_supported_claim_has_high_lexical_coverage():
    """A recommendation closely matching the source should pass the lexical check."""

    source = Chunk("abc", "approved_playbook.md", "Liability Cap", "Liability cap is limited to 1.0x annual fees.", 1)
    label, reason = evaluate_groundedness("Liability cap is limited to 1.0x annual fees.", [source])
    assert label == "SUPPORTED"
    assert "coverage" in reason


def test_uncited_claim_is_not_supported():
    """Claims without source evidence must fail closed."""

    label, _ = evaluate_groundedness("Liability cap is 0.5x annual fees.", [])
    assert label == "NOT_SUPPORTED"


def test_unrelated_source_is_not_supported():
    """A source about renewal should not support a liability claim."""

    source = Chunk("xyz", "approved_playbook.md", "Renewal", "The agreement renews annually with 60 days notice.", 1)
    label, _ = evaluate_groundedness("Liability cap is 0.5x annual fees.", [source])
    assert label == "NOT_SUPPORTED"
