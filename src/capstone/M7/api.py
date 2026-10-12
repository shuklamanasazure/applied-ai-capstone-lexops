import asyncio  # Run blocking graph execution away from the event loop.
from fastapi import FastAPI, HTTPException  # Expose an HTTP endpoint with controlled errors.
from .schemas import ReviewRequest, ReviewResult  # Validate input and output.
from .workflow import run_review  # Reuse the LangGraph pipeline.

app = FastAPI(title="LexOps M7", version="0.1.0")  # Create the reusable FastAPI application.


@app.get("/health")
async def health() -> dict:
    # Lightweight health check for local development and container probes.
    return {"status": "ok"}


@app.post("/reviews", response_model=ReviewResult)
async def create_review(request: ReviewRequest) -> ReviewResult:
    # Bound the overall review time; each real external dependency should also have its own timeout.
    try:
        # run_review is synchronous because the demo LangGraph nodes are synchronous.
        return await asyncio.wait_for(asyncio.to_thread(run_review, request), timeout=60.0)
    except TimeoutError as exc:
        # Do not return a false success when the overall review exceeds its deadline.
        raise HTTPException(
            status_code=504,
            detail={"code": "review_timeout", "review_id": request.review_id},
        ) from exc
    except Exception as exc:
        # Avoid exposing internal exception details or contract content to API clients.
        raise HTTPException(
            status_code=500,
            detail={"code": "review_failed", "review_id": request.review_id},
        ) from exc
