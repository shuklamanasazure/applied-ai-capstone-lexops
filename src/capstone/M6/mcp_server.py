
# Launch the MCP server using the project's Python environment.
# PYTHONPATH=src uv run python -m capstone.M6.mcp_server


# src/capstone/M6/mcp_server.py

from mcp.server.fastmcp import FastMCP  # Create an MCP tool server.
from capstone.M6.repository import ContractRepository  # Reuse the adapter.

# Create the MCP server with a descriptive name.
mcp = FastMCP("LexOps Contract Repository")

# Create the repository adapter.
repository = ContractRepository()


@mcp.tool()
def get_contract(contract_id: str) -> dict:
    # Expose contract lookup as a business capability.
    return repository.get_contract(contract_id)


@mcp.tool()
def list_contracts() -> list[dict]:
    # Expose contract listing without exposing file-system paths.
    return repository.list_contracts()


@mcp.tool()
def search_contracts(query: str) -> list[dict]:
    # Expose simple repository search.
    return repository.search_contracts(query)


@mcp.tool()
def get_counterparty(counterparty_id: str) -> dict:
    # Expose counterparty details or history fixtures.
    return repository.get_counterparty(counterparty_id)


@mcp.tool()
def get_envelope(envelope_id: str) -> dict:
    # Expose read-only e-signature envelope details.
    return repository.get_envelope(envelope_id)


@mcp.tool()
def envelope_status(envelope_id: str) -> str:
    # Expose the current mock signature status.
    return repository.envelope_status(envelope_id)


if __name__ == "__main__":
    # Start the server over stdio for compatible MCP clients.
    mcp.run(transport="stdio")