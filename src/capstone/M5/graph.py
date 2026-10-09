# Import the graph builder and workflow start/end markers.
from langgraph.graph import StateGraph, START, END

# Import the checkpoint implementation for local development.
from langgraph.checkpoint.memory import InMemorySaver

# Import the retry policy used for transient node failures.
from langgraph.types import RetryPolicy

# Import all workflow node functions.
from capstone.m5.nodes import (
    extract_node,
    compare_node,
    risk_node,
    draft_redline_node,
    prepare_standard_node,
    human_review_node,
    finalize_node,
)


# Define the data passed between nodes.
class ReviewState(dict):
    """Document the state shape conceptually; graph nodes use dictionary fields."""


# Select the next node using deterministic Python policy.
def route_by_risk(state: dict) -> str:
    # Send standard contracts to the preparation node.
    if state["risk_level"] == "standard":
        return "prepare_standard"

    # Send non-standard contracts to redline drafting.
    return "draft_redline"


# Construct the reusable graph.
def build_graph(checkpointer=None):
    # Create a typed graph builder using the dictionary-based state.
    builder = StateGraph(dict)

    # Register clause extraction and retry transient failures.
    builder.add_node(
        "extract",
        extract_node,
        retry_policy=RetryPolicy(max_attempts=3),
    )

    # Register playbook comparison.
    builder.add_node("compare", compare_node)

    # Register deterministic risk assessment.
    builder.add_node("risk", risk_node)

    # Register standard-path preparation.
    builder.add_node("prepare_standard", prepare_standard_node)

    # Register redline drafting.
    builder.add_node("draft_redline", draft_redline_node)

    # Register the human approval interrupt.
    builder.add_node("human_review", human_review_node)

    # Register final review package generation.
    builder.add_node("finalize", finalize_node)

    # Start by extracting the contract clauses.
    builder.add_edge(START, "extract")

    # Compare clauses after extraction.
    builder.add_edge("extract", "compare")

    # Assess risk after comparison.
    builder.add_edge("compare", "risk")

    # Select the next node based on the risk classification.
    builder.add_conditional_edges(
        "risk",
        route_by_risk,
        {
            "prepare_standard": "prepare_standard",
            "draft_redline": "draft_redline",
        },
    )

    # Complete standard-path preparation by finalizing the package.
    builder.add_edge("prepare_standard", "finalize")

    # Request human approval after drafting a non-standard redline.
    builder.add_edge("draft_redline", "human_review")

    # Finalize only after the human review node returns a decision.
    builder.add_edge("human_review", "finalize")

    # End the workflow after finalization.
    builder.add_edge("finalize", END)

    # Use the supplied checkpointer or an in-memory development default.
    saver = checkpointer if checkpointer is not None else InMemorySaver()

    # Compile the graph with checkpointing enabled.
    return builder.compile(checkpointer=saver)