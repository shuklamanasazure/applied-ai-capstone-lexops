# Import the test client.
from fastapi.testclient import TestClient

# Import the application.
from capstone.m5.api import app


# Create a client for exercising the API without starting a server.
client = TestClient(app)


# Test that the standard review endpoint returns a final package.
def test_standard_review_api():
    # Submit a contract with no non-standard clause headings.
    response = client.post(
        "/reviews",
        json={
            "review_id": "API-001",
            "counterparty": "Northwind",
            "contract": "Standard contract wording.",
        },
    )

    # Verify the HTTP response and workflow outcome.
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["review_package"]["decision"] == "auto_approved"


# Test that a high-risk review can be approved through the API.
def test_human_approval_api():
    # Start a review with a non-standard liability clause.
    started = client.post(
        "/reviews",
        json={
            "review_id": "API-002",
            "counterparty": "CyberShield",
            "contract": "liability: unlimited",
        },
    )

    # Confirm that the workflow paused for human approval.
    assert started.status_code == 200
    assert started.json()["status"] == "pending_human_approval"

    # Submit the lawyer's decision to resume the checkpoint.
    approved = client.post(
        "/reviews/API-002/approval",
        json={
            "decision": "approve",
            "reviewer": "lawyer@example.test",
            "comment": "Reviewed the proposed changes.",
        },
    )

    # Verify that the graph resumed and finalized successfully.
    assert approved.status_code == 200
    assert approved.json()["review_package"]["decision"] == "human_approved"