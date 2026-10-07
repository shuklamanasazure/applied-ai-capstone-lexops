# Import FastAPI.
from fastapi import FastAPI

# Import the agent.
from .agent import review_contract

# Import the API request and response models.
from .models import ReviewRequest, ReviewResponse


# Create the FastAPI application.
app = FastAPI(
    title="LexOps M2",
    description="Single-agent contract review with tools",
    version="0.2.0",
)


@app.get("/M2health")
def health():
    return {"status": "ok"}


# Create the contract-review endpoint.
@app.post(
    "/review",
    response_model=ReviewResponse,
)
def review(
    request: ReviewRequest,
) -> ReviewResponse:

    # Send the request to the single LexOps agent.
    return review_contract(request)