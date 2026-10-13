"""Tests for file ingestion and chunk provenance."""

from pathlib import Path  # Build a temporary corpus.
from lexops_m4.corpus import load_corpus  # Test corpus loading.


def test_load_corpus_creates_traceable_chunks(tmp_path: Path):
    """Markdown heading and file path should survive ingestion."""

    file = tmp_path / "approved_playbook.md"
    file.write_text("# Liability Cap\nThe liability cap is limited to 1.0x annual fees and excludes indirect damages.", encoding="utf-8")
    chunks = load_corpus(tmp_path, min_chunk_chars=10)
    assert chunks
    assert chunks[0].document == "approved_playbook.md"
    assert chunks[0].section == "Liability Cap"
    assert chunks[0].authority_rank == 1
