
# src/capstone/M6/agents.py

from capstone.M6.repository import ContractRepository  # Read mock contracts.
from capstone.M6.schemas import (  # Import validated output contracts.
    Clause, ContractSummary, PlaybookFinding,
    RedlineProposal, LegalDecision,
)

# Configure sample approved standards and fallback language.
PLAYBOOK = {
    "termination": {
        "standard": "Either party may terminate with 30 days notice.",
        "fallback": "Either party may terminate with 60 days notice.",
        "source": "playbook/termination.md",
    },
    "liability": {
        "standard": "Liability is capped at fees paid in 12 months.",
        "fallback": "Liability is capped at fees paid in 24 months.",
        "source": "playbook/liability.md",
    },
}


class ExtractionAgent:
    # Locate and normalize clauses; never assess risk.

    def __init__(self, repository: ContractRepository):
        self.repository = repository

    def run(self, contract_id: str) -> ContractSummary:
        # Retrieve the requested contract.
        record = self.repository.get_contract(contract_id)

        # Normalize the repository's expected contract text field.
        text = str(record.get("contract_text", ""))

        # Locate supported clause headings in a simple demo.
        clauses = []
        for name in PLAYBOOK:
            # Search the contract for a matching clause keyword.
            position = text.casefold().find(name)
            if position >= 0:
                # Extract a simple sentence-sized section for the demo.
                end = text.find(".", position)
                clause_text = text[position:end + 1] if end >= 0 else text[position:]
                clauses.append(
                    Clause(name=name, text=clause_text.strip())
                )

        # Return normalized extraction data, without a risk score.
        return ContractSummary(
            contract_id=contract_id,
            counterparty_id=str(record.get("counterparty_id", "unknown")),
            clauses=clauses,
        )


class PlaybookRAGAgent:
    # Compare extracted clauses with approved standards and cite sources.

    def run(self, summary: ContractSummary) -> list[PlaybookFinding]:
        findings = []

        # Process each extracted clause independently.
        for clause in summary.clauses:
            policy = PLAYBOOK.get(clause.name)

            # Missing authoritative material requires a review.
            if policy is None:
                findings.append(
                    PlaybookFinding(
                        clause_name=clause.name,
                        standard_text="No matching standard found.",
                        fallback_text="",
                        source="not-found",
                        deviation=True,
                    )
                )
                continue

            # Compare wording with the configured standard.
            deviation = (
                clause.text.casefold()
                != policy["standard"].casefold()
            )

            # Return evidence; do not write a redline here.
            findings.append(
                PlaybookFinding(
                    clause_name=clause.name,
                    standard_text=policy["standard"],
                    fallback_text=policy["fallback"],
                    source=policy["source"],
                    deviation=deviation,
                )
            )

        return findings


class RedlineDrafter:
    # Draft suggested language; never approve it.

    def run(
        self,
        summary: ContractSummary,
        findings: list[PlaybookFinding],
    ) -> list[RedlineProposal]:
        proposals = []

        # Match comparison evidence to each extracted clause.
        for finding in findings:
            clause = next(
                (c for c in summary.clauses
                 if c.name == finding.clause_name),
                None,
            )

            # Do not fabricate a proposal without original wording.
            if clause is None or not finding.deviation:
                continue

            # Use the approved fallback as the proposed wording.
            proposals.append(
                RedlineProposal(
                    clause_name=clause.name,
                    original_text=clause.text,
                    proposed_text=finding.fallback_text,
                    explanation=(
                        "The contract wording differs from the "
                        "approved playbook standard."
                    ),
                    approved_fallback=finding.fallback_text,
                )
            )

        return proposals


class LegalReviewer:
    # Inspect all outputs and determine the review route.

    def run(
        self,
        summary: ContractSummary,
        findings: list[PlaybookFinding],
        redlines: list[RedlineProposal],
    ) -> LegalDecision:
        reasons = []

        # Missing clauses or missing authoritative standards need review.
        if not summary.clauses:
            reasons.append("No supported clauses were extracted.")

        if any(f.source == "not-found" for f in findings):
            reasons.append("Authoritative playbook evidence is missing.")

        # Deviations need human review in this conservative starter policy.
        if any(f.deviation for f in findings):
            reasons.append("One or more clauses deviate from the playbook.")

        # Every proposed redline must have a valid fallback reference.
        if any(not r.approved_fallback for r in redlines):
            reasons.append("A proposed redline lacks fallback wording.")

        # Return a decision; never execute a signature action.
        if reasons:
            return LegalDecision(
                status="human_review",
                reasons=reasons,
            )

        return LegalDecision(
            status="auto_approve",
            reasons=["All evaluated clauses match configured standards."],
        )