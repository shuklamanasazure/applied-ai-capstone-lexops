
# src/capstone/M6/main.py

from fastapi import FastAPI, HTTPException  # Create the HTTP API.
from pydantic import BaseModel  # Validate the response model.
from capstone.M6.schemas import ReviewRequest  # Validate the request.
from capstone.M6.graph import review_graph  # Reuse the compiled graph.
from capstone.M6.repository import ContractRepository  # Check contract IDs.

# Create the FastAPI application.
app = FastAPI(title="LexOps M6 Multi-Agent API")

# Use the repository to validate the requested identifier.
repository = ContractRepository()


class ReviewResponse(BaseModel):
    # Define the structured API response.
    contract_id: str
    summary: dict
    findings: list[dict]
    redlines: list[dict]
    decision: dict


@app.get("/M6health")
def health():
    # Provide a basic health-check endpoint.
    return {"status": "ok", "module": "M6"}


@app.post("/reviews", response_model=ReviewResponse)
def review_contract(request: ReviewRequest):
    # Reject unknown contract IDs before starting the graph.
    try:
        repository.get_contract(request.contract_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Give each contract review a stable checkpoint thread identifier.
    config = {
        "configurable": {
            "thread_id": f"review-{request.contract_id}"
        }
    }

    # Invoke the supervisor workflow.
    try:
        result = review_graph.invoke(
            {"contract_id": request.contract_id},
            config=config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Return only the fields required by the API contract.
    return ReviewResponse(
        contract_id=request.contract_id,
        summary=result["summary"],
        findings=result["findings"],
        redlines=result["redlines"],
        decision=result["decision"],
    )