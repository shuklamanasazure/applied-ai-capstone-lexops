
# src/capstone/M6/graph.py

from langgraph.graph import StateGraph, START, END  # Define workflow edges.
from langgraph.checkpoint.memory import InMemorySaver  # Save graph state.

from capstone.M6.schemas import ReviewState  # Define shared state.
from capstone.M6.repository import ContractRepository  # Access mock data.
from capstone.M6.agents import (  # Instantiate the four agents.
    ExtractionAgent, PlaybookRAGAgent,
    RedlineDrafter, LegalReviewer,
)


def build_graph(checkpointer=None):
    # Build a reusable graph; allow a checkpointer to be injected.
    repository = ContractRepository()

    # Create each specialist independently.
    extractor = ExtractionAgent(repository)
    rag = PlaybookRAGAgent()
    drafter = RedlineDrafter()
    reviewer = LegalReviewer()

    def extract_node(state: ReviewState) -> dict:
        # Extract and normalize the contract.
        record = repository.get_contract(state["contract_id"])
        summary = extractor.run(state["contract_id"])

        # Return only this node's state updates.
        return {
            "contract_text": str(record.get("contract_text", "")),
            "counterparty_id": summary.counterparty_id,
            "summary": summary.model_dump(),
        }

    def playbook_node(state: ReviewState) -> dict:
        # Validate prior output and compare with the playbook.
        from capstone.M6.schemas import ContractSummary
        summary = ContractSummary.model_validate(state["summary"])
        findings = rag.run(summary)
        return {"findings": [f.model_dump() for f in findings]}

    def redline_node(state: ReviewState) -> dict:
        # Rebuild typed objects from shared state.
        from capstone.M6.schemas import ContractSummary, PlaybookFinding
        summary = ContractSummary.model_validate(state["summary"])
        findings = [
            PlaybookFinding.model_validate(f) for f in state["findings"]
        ]

        # Generate proposals, without making approval decisions.
        redlines = drafter.run(summary, findings)
        return {"redlines": [r.model_dump() for r in redlines]}

    def review_node(state: ReviewState) -> dict:
        # Validate all agent outputs before legal review.
        from capstone.M6.schemas import (
            ContractSummary, PlaybookFinding, RedlineProposal,
        )
        summary = ContractSummary.model_validate(state["summary"])
        findings = [
            PlaybookFinding.model_validate(f) for f in state["findings"]
        ]
        redlines = [
            RedlineProposal.model_validate(r) for r in state["redlines"]
        ]

        # Only the legal reviewer creates the final status.
        decision = reviewer.run(summary, findings, redlines)
        return {"decision": decision.model_dump()}

    # Declare the four specialist nodes.
    builder = StateGraph(ReviewState)
    builder.add_node("extract", extract_node)
    builder.add_node("playbook", playbook_node)
    builder.add_node("redline", redline_node)
    builder.add_node("legal_review", review_node)

    # Define the sequential supervisor-controlled workflow.
    builder.add_edge(START, "extract")
    builder.add_edge("extract", "playbook")
    builder.add_edge("playbook", "redline")
    builder.add_edge("redline", "legal_review")
    builder.add_edge("legal_review", END)

    # Use the supplied checkpointer or a local in-memory default.
    return builder.compile(
        checkpointer=checkpointer or InMemorySaver()
    )


# Create a reusable graph instance for application imports.
review_graph = build_graph()