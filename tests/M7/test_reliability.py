import asyncio  # Simulate asynchronous dependency behavior.
import pytest  # Provide async tests and exception assertions.
from pydantic import BaseModel  # Create a minimal structured-output schema.
from capstone.M7.reliability import retry_async, ControlledFailure, parse_large_document, validate_or_fail


@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_timeout():
    # Count attempts to prove that a transient failure is retried.
    calls = 0

    async def operation():
        # Fail once, then succeed on the second call.
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("temporary")
        return "ok"

    # Use zero backoff to keep the test fast and deterministic.
    result = await retry_async(operation, max_attempts=2, base_delay_seconds=0)
    assert result == "ok"
    assert calls == 2


@pytest.mark.asyncio
async def test_retry_stops_after_limit():
    # An always-failing dependency should not be retried forever.
    async def operation():
        raise TimeoutError("temporary")

    with pytest.raises(ControlledFailure):
        await retry_async(operation, max_attempts=2, base_delay_seconds=0)


def test_long_document_is_segmented():
    # Long content should be split into bounded chunks.
    sections = parse_large_document(("termination clause. " * 500), max_chars_per_section=1000)
    assert len(sections) > 1
    assert all(len(section) <= 1000 for section in sections)


def test_empty_document_fails_closed():
    # Empty text must not be treated as a valid contract.
    with pytest.raises(ControlledFailure, match="document_empty"):
        parse_large_document("   ")


def test_invalid_structured_output_fails_closed():
    # Define a schema with a required integer field.
    class Output(BaseModel):
        risk_score: int

    # Invalid model output should raise a controlled failure, not become a fake success.
    with pytest.raises(ControlledFailure, match="human_review_required"):
        validate_or_fail({"risk_score": "not-an-integer"}, Output)
