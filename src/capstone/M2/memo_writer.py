# Import Path for safe filesystem handling.
from pathlib import Path

# Import the memo input/output models.
from .models import MemoRequest, MemoResult


# Create the text content of the review memo.
def create_memo_content(request: MemoRequest) -> str:

    # Start with the contract heading.
    lines = [
        "# LexOps Contract Review Memo",
        "",
        f"Contract ID: {request.contract.contract_id}",
        f"Counterparty: {request.contract.counterparty}",
        f"Contract Value: ${request.contract.contract_value:,.2f}",
        "",
        "## Contract",
        "",
        request.contract.description,
        "",
        "## Clause Risks",
        "",
    ]

    # Add every risk result to the memo.
    for risk in request.risks:

        # Add the clause information.
        lines.append(
            f"- {risk.clause_type}: "
            f"{risk.risk_level} risk "
            f"(score={risk.risk_score}, "
            f"deviation={risk.deviation}%)."
        )

        # Add the explanation.
        lines.append(
            f"  Explanation: {risk.explanation}"
        )

    # Add renewal information.
    lines.extend(
        [
            "",
            "## Renewal",
            "",
            f"Renewal Date: {request.renewal.renewal_date}",
            f"Notice Deadline: {request.renewal.notice_deadline}",
            f"Urgency: {request.renewal.urgency}",
            "",
            "## Agent Guardrail",
            "",
            "This memo is for internal review only.",
            "The LexOps agent does not approve, execute,",
            "or communicate legal commitments.",
        ]
    )

    # Combine all lines into one text document.
    return "\n".join(lines)


# Save the generated memo to a file.
def write_review_memo(
    request: MemoRequest,
    output_directory: str = "output",
) -> MemoResult:

    # Generate the memo content first.
    content = create_memo_content(request)

    # Convert the output directory into a Path object.
    output_path = Path(output_directory)

    # Create the directory if it does not exist.
    output_path.mkdir(parents=True, exist_ok=True)

    # Build the filename using the contract ID.
    file_path = (
        output_path
        / f"{request.contract.contract_id}_review.md"
    )

    # Write the memo to disk.
    file_path.write_text(
        content,
        encoding="utf-8",
    )

    # Return both the path and generated content.
    return MemoResult(
        file_path=str(file_path),
        content=content,
    )