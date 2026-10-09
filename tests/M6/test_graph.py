# tests/M6/test_graph.py

from langgraph.checkpoint.memory import InMemorySaver
from capstone.M6.graph import build_graph


def test_graph_is_compiled_with_checkpointing():
    # Build an independent graph for this test.
    graph = build_graph(checkpointer=InMemorySaver())

    # Confirm that a compiled graph is returned.
    assert graph is not None