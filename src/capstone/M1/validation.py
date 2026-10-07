# Import the ContractSummary model.
from .models import ContractSummary


# Normalize text so that small whitespace differences
# do not cause a false validation failure.
def normalize_text(text: str) -> str:

    # Split removes repeated spaces/newlines.
    # Join creates a normalized representation.
    return " ".join(text.split())


# Validate that extracted source text actually exists
# in the original contract.
def validate_provenance(
    summary: ContractSummary,
    contract_text: str,
) -> None:

    # Normalize the original contract.
    normalized_contract = normalize_text(contract_text)

    # Put all five clauses into one collection.
    clauses = [
        summary.term,
        summary.termination,
        summary.liability_cap,
        summary.indemnification,
        summary.governing_law,
    ]

    # Check every extracted clause.
    for clause in clauses:

        # A null raw_text means that the clause was not found.
        if clause.raw_text is None:
            continue

        # Normalize the extracted source text.
        normalized_clause = normalize_text(clause.raw_text)

        # Check whether the extracted text actually exists
        # in the original contract.
        if normalized_clause not in normalized_contract:

            # Stop processing because the LLM produced
            # source text that cannot be found in the contract.
            raise ValueError(
                "Extracted raw_text was not found in the "
                "original contract."
            )