# This adapter reads the mock API files and provides controlled business operations. It keeps file-system details out of the agents.

# Because I cannot inspect the contents of your local ./data/lexops/mock_api directory from this message, the example below assumes 
# contract records are JSON files containing a contract ID, counterparty ID, and contract text. Update the mapping if your existing fixtures use 
# different field names.


# src/capstone/M6/repository.py

import json  # Read JSON fixtures.
from pathlib import Path  # Handle repository paths safely.


class ContractRepository:
    # Encapsulate mock data access in one reusable class.

    def __init__(self, root: str = "./data/lexops/mock_api"):
        # Store the configured mock API data directory.
        self.root = Path(root)

    def _records(self) -> list[dict]:
        # Load JSON records from the configured directory.
        records = []
        for path in self.root.rglob("*.json"):
            # Read each JSON fixture.
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                # Ignore unreadable or invalid JSON files.
                continue

            # Accept a single record or a list of records.
            if isinstance(data, dict):
                records.append(data)
            elif isinstance(data, list):
                records.extend(item for item in data
                               if isinstance(item, dict))
        return records

    def get_contract(self, contract_id: str) -> dict:
        # Find a contract by its business identifier.
        for record in self._records():
            if str(record.get("contract_id", "")) == contract_id:
                return record
        # Report missing records explicitly.
        raise ValueError(f"Contract not found: {contract_id}")

    def list_contracts(self) -> list[dict]:
        # Return contract-like records with identifiers.
        return [
            record for record in self._records()
            if "contract_id" in record
        ]

    def search_contracts(self, query: str) -> list[dict]:
        # Search contract records using a simple case-insensitive match.
        term = query.casefold()
        return [
            record for record in self.list_contracts()
            if term in json.dumps(record).casefold()
        ]

    def get_counterparty(self, counterparty_id: str) -> dict:
        # Find a record for a counterparty.
        for record in self._records():
            if str(record.get("counterparty_id", "")) == counterparty_id:
                return record
        raise ValueError(f"Counterparty not found: {counterparty_id}")

    def get_envelope(self, envelope_id: str) -> dict:
        # Find the mock e-signature envelope.
        for record in self._records():
            if str(record.get("envelope_id", "")) == envelope_id:
                return record
        raise ValueError(f"Envelope not found: {envelope_id}")

    def envelope_status(self, envelope_id: str) -> str:
        # Return status without performing a signature action.
        envelope = self.get_envelope(envelope_id)
        return str(envelope.get("status", "unknown"))