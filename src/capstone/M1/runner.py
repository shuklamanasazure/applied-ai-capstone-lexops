# To Process your 200 JSONL contracts stored in  "data/lexops/intake/records.jsonl", Execute uv run python -m capstone.M1.runner

# Import json to read JSONL records.
import json

# Import Path for clean file handling.
from pathlib import Path

# Import our input model.
from .models import ContractReviewRequest

# Import our reusable extractor.
from .extractor import extract_contract


# Location of the input JSONL file.
INPUT_FILE = Path(
    "data/lexops/intake/records.jsonl"
)


# Process all contracts in the JSONL file.
def process_contracts() -> None:

    # Open the JSONL file.
    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        # Process one contract at a time.
        for line_number, line in enumerate(
            file,
            start=1,
        ):

            # Convert the JSON text into a Python dictionary.
            record = json.loads(line)

            # Convert the raw record into our controlled input contract.
            request = ContractReviewRequest(
                contract_id=record["record_id"],
                counterparty=record["counterparty_name"],
                contract_text=record["attached_clause_text"],
            )

            # Extract the five required clauses.
            summary = extract_contract(request)

            # Print the validated result.
            print(summary.model_dump_json(indent=2))

            # Show progress.
            print(
                f"Processed contract {line_number}: "
                f"{request.contract_id}"
            )


# Run the batch processor when this file is executed directly.
if __name__ == "__main__":

    # Start processing the JSONL contracts.
    process_contracts()  