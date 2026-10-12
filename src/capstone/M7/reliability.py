import asyncio  # Provide async timeouts and backoff delays.
from collections.abc import Awaitable, Callable  # Type hints for reusable async operations.
from typing import TypeVar  # Preserve the return type of retried operations.
from pydantic import BaseModel, ValidationError  # Validate structured model output.

T = TypeVar("T")  # Generic result type for retry_async.


class ControlledFailure(RuntimeError):
    # Represents a known, safe-to-handle failure instead of an unhandled crash.
    pass


async def retry_async(
    operation: Callable[[], Awaitable[T]],  # Callable that creates a fresh awaitable per attempt.
    *, timeout_seconds: float = 10.0,  # Maximum duration allowed for each attempt.
    max_attempts: int = 3,  # Total attempts, including the first attempt.
    base_delay_seconds: float = 0.25,  # Initial backoff delay; exponential backoff follows.
) -> T:
    # Fail fast on invalid retry configuration.
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    # Retry only timeout and connection-style failures; don't retry arbitrary programming errors.
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            # Bound every attempt; asyncio.wait_for cancels the awaitable on timeout.
            return await asyncio.wait_for(operation(), timeout=timeout_seconds)
        except (TimeoutError, asyncio.TimeoutError, ConnectionError) as exc:
            # Retain the final exception for a useful controlled failure.
            last_error = exc
            # Do not sleep after the final attempt.
            if attempt == max_attempts - 1:
                break
            # Exponential backoff: 0.25s, 0.5s, 1s by default.
            await asyncio.sleep(base_delay_seconds * (2 ** attempt))

    # Raise a sanitized failure without returning a fake success result.
    raise ControlledFailure(
        f"dependency_failed_after_{max_attempts}_attempts"
    ) from last_error


def parse_large_document(text: str, *, max_chars_per_section: int = 6000) -> list[str]:
    # Reject empty content rather than treating it as a valid contract.
    if not text.strip():
        raise ControlledFailure("document_empty")

    # Split by blank lines as a simple learning baseline; production should use a PDF parser
    # and page/heading/clause boundaries while preserving page references.
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    sections: list[str] = []
    current = ""

    # Accumulate paragraphs into bounded sections without exceeding the target size where possible.
    for paragraph in paragraphs:
        # Split unusually long paragraphs so one paragraph cannot bypass the size limit.
        chunks = [
            paragraph[i : i + max_chars_per_section]
            for i in range(0, len(paragraph), max_chars_per_section)
        ]
        for chunk in chunks:
            if current and len(current) + len(chunk) + 2 > max_chars_per_section:
                sections.append(current)
                current = ""
            current = f"{current}\n\n{chunk}".strip()

    # Keep the final section.
    if current:
        sections.append(current)

    # Return bounded pieces for targeted extraction and merging.
    return sections


def validate_or_fail(raw: dict, schema: type[BaseModel]) -> BaseModel:
    # Validate structured output using the requested Pydantic v2 schema.
    try:
        return schema.model_validate(raw)
    except ValidationError as exc:
        # Do not silently coerce invalid output into an apparently successful result.
        # A production workflow can retry with a repair prompt, then route to human review.
        raise ControlledFailure("llm_structured_output_invalid_human_review_required") from exc
