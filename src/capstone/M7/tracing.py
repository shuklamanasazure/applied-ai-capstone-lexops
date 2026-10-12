import os  # Read configuration from environment variables.
from contextlib import contextmanager  # Provide a no-op fallback if tracing is disabled.
from langfuse import get_client, observe, propagate_attributes  # Langfuse Python SDK v4 APIs.

MODEL_NAME = os.getenv("LEXOPS_MODEL", "claude-sonnet")  # Store the model label for trace metadata.
PROMPT_VERSION = os.getenv("LEXOPS_PROMPT_VERSION", "contract-review-v1")  # Version prompts explicitly.

# get_client() reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and LANGFUSE_BASE_URL.
# With valid credentials, @observe creates hierarchical observations; keep input/output capture off.
langfuse = get_client()


@contextmanager
def review_trace_attributes(review_id: str, contract_id: str, counterparty: str):
    # Propagate safe correlation metadata to the trace and child observations.
    # Do not include document_text, clauses, secrets, or full prompts in metadata.
    with propagate_attributes(
        trace_name="LexOps Contract Review",
        session_id=review_id,
        metadata={
            "review_id": review_id[:120],
            "contract_id": contract_id[:120],
            "counterparty": counterparty[:120],
            "model": MODEL_NAME,
            "prompt_version": PROMPT_VERSION,
        },
        tags=["lexops", "m7", "contract-review"],
    ):
        yield
