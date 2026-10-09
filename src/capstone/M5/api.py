# Import FastAPI components.
from fastapi import FastAPI, HTTPException

# Import LangGraph's resume command.
from langgraph.types import Command

# Import request schemas.
from capstone.M5.schemas import ReviewRequest, ApprovalRequest

# Import the graph factory.
from capstone.M5.graph import build_graph


# Create the HTTP application.
app = FastAPI(title="LexOps M5 Contract Review")

# Compile one graph instance for the application lifetime.
graph = build_graph()


# Build the configuration used to find a review's checkpoint.
def review_config(review_id: str) -> dict:
    # Use the same stable thread ID for start, lookup, and resume.
    return {"configurable": {"thread_id": review_id}}


@app.get("/M5health")
def health() -> dict:
    # Provide a simple health endpoint for local testing.
    return {"status": "ok"}


# Start a new contract review.
@app.post("/reviews")
def start_review(request: ReviewRequest):
    # Build the initial graph state from the validated request.
    initial_state = {
        "review_id": request.review_id,
        "counterparty": request.counterparty,
        "contract": request.contract,
        "audit_events": [],
    }

    # Run the workflow until it finishes or reaches an interrupt.
    result = graph.invoke(
        initial_state,
        config=review_config(request.review_id),
    )

    # Report a pending human decision when execution is interrupted.
    if result.get("__interrupt__"):
        return {
            "review_id": request.review_id,
            "status": "pending_human_approval",
            "interrupt": [
                item.value for item in result["__interrupt__"]
            ],
        }

    # Return the final package when no interruption occurred.
    return {
        "review_id": request.review_id,
        "status": "completed",
        "review_package": result.get("review_package"),
    }


# Read the latest checkpointed state for a review.
@app.get("/reviews/{review_id}")
def get_review(review_id: str):
    # Retrieve the checkpoint using the stable review ID.
    snapshot = graph.get_state(review_config(review_id))

    # Return a 404 when no checkpoint exists for the review.
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Review not found")

    # Detect whether LangGraph is waiting for human input.
    pending = bool(snapshot.next)

    # Return a useful state projection rather than internal objects.
    return {
        "review_id": review_id,
        "status": "pending_human_approval" if pending else "completed",
        "state": snapshot.values,
        "next_nodes": list(snapshot.next),
    }


# Resume a paused review with a validated human decision.
@app.post("/reviews/{review_id}/approval")
def approve_review(review_id: str, request: ApprovalRequest):
    # Retrieve the saved checkpoint before resuming.
    snapshot = graph.get_state(review_config(review_id))

    # Reject reviews that do not exist.
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Review not found")

    # Reject reviews that are not waiting for human approval.
    if "human_review" not in snapshot.next:
        raise HTTPException(
            status_code=409,
            detail="Review is not awaiting human approval",
        )

    # Resume the exact suspended node with the validated decision.
    result = graph.invoke(
        Command(resume=request.model_dump()),
        config=review_config(review_id),
    )

    # Return the finalized package and decision.
    return {
        "review_id": review_id,
        "status": "completed",
        "review_package": result.get("review_package"),
    }  