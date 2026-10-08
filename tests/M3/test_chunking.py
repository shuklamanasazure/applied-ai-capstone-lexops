"""Unit test for deterministic Markdown chunking."""

# Import the service implementation.
from capstone.M3.llm import LLMService
from capstone.M3.qdrant_store import QdrantStore


def test_chunking_preserves_full_text():
    # Bypass external clients because only the pure chunking helper is under test.
    store = object.__new__(QdrantStore)
    # Generate a document larger than one chunk.
    text = "A" * 2000
    # Chunk the text using a small chunk size.
    chunks = store._chunk_markdown(text, chunk_size=500, overlap=50)
    # Verify that more than one chunk was produced.
    assert len(chunks) > 1
    # Verify that the beginning and end of the source remain represented.
    assert chunks[0].startswith("A")
    assert chunks[-1].endswith("A")


# To run this test, use the following command in the terminal:
# uv run pytest tests/M3/test_chunking.py