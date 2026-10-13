"""Deterministic citation-groundedness checks; not a substitute for legal review."""

import re  # Tokenize recommendation and source evidence.
from capstone.M4.corpus import Chunk  # Source evidence type.


def terms(text: str) -> set[str]:
    """Normalize words and numbers for a transparent lexical support check."""

    return set(re.findall(r"[a-z0-9]+(?:\\.[0-9]+)?", text.lower()))  # Keep numeric terms such as 0.5.


def evaluate_groundedness(recommendation: str, citations: list[Chunk]) -> tuple[str, str]:
    """Label evidence support based on recommendation-term coverage in cited source text."""

    claim_terms = terms(recommendation) - {"the", "a", "an", "is", "are", "to", "of", "and", "or", "in", "for"}
    if not claim_terms:
        return "NOT_SUPPORTED", "Recommendation contains no meaningful terms to verify."  # Fail closed.
    if not citations:
        return "NOT_SUPPORTED", "No source citations were retrieved."  # Never trust uncited generated text.
    evidence_terms = set().union(*(terms(chunk.text) for chunk in citations))  # Combine cited source evidence.
    coverage = len(claim_terms & evidence_terms) / len(claim_terms)  # Fraction of claim terms found in evidence.
    if coverage >= 0.80:
        return "SUPPORTED", f"Deterministic lexical coverage is {coverage:.0%}; manually verify semantic entailment."
    if coverage >= 0.45:
        return "PARTIALLY_SUPPORTED", f"Deterministic lexical coverage is {coverage:.0%}; review missing claim terms."
    return "NOT_SUPPORTED", f"Deterministic lexical coverage is only {coverage:.0%}; do not rely on this recommendation."


def draft_recommendation(query: str, chunks: list[Chunk]) -> str:
    """Produce a conservative evidence-first summary without pretending to be an LLM."""

    if not chunks:
        return "No recommendation can be made because no source evidence was retrieved."
    primary = chunks[0]  # Use the top ranked evidence as the starting point.
    if primary.authority_rank != 1:
        return f"Potentially relevant text was found in {primary.document}, but no authoritative playbook passage is confirmed."
    return f"Review the clause against the playbook section '{primary.section}'. Retrieved evidence: {primary.text[:500]}"


def build_answer(query: str, ranked: list[tuple[Chunk, float]]) -> dict:
    """Attach exact citations and evaluate the answer against the cited source passages."""

    chunks = [chunk for chunk, _score in ranked]  # Evidence supplied to the recommendation.
    recommendation = draft_recommendation(query, chunks)  # Keep answer constrained to retrieved evidence.
    label, reason = evaluate_groundedness(recommendation, chunks)  # Verify the draft against its citations.
    return {
        "recommendation": recommendation,  # Return the source-based summary.
        "citations": [
            {
                "source_document": chunk.document,  # Original relative file path.
                "source_section": chunk.section,  # Source heading.
                "source_chunk": chunk.chunk_id,  # Stable chunk ID.
                "source_text": chunk.text,  # Exact evidence text.
                "authority_rank": chunk.authority_rank,  # Show source authority.
                "score": float(score),  # Ranking score for traceability.
            }
            for chunk, score in ranked
        ],
        "groundedness": label,  # One of the three required labels.
        "groundedness_reason": reason,  # Transparent deterministic result.
    }
