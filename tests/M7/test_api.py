from fastapi.testclient import TestClient  # Exercise the HTTP API without starting a server.
from capstone.M7.api import app  # Import the application under test.

client = TestClient(app)  # Create an in-process test client.


def test_health_endpoint():
    # Health endpoint should be available without external services.
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_review_endpoint_returns_validated_result():
    # Send a small demo contract containing one relevant clause.
    response = client.post("/reviews", json={
        "review_id": "review-test-001",
        "contract_id": "contract-test-001",
        "counterparty": "Example Co",
        "document_text": "Termination: either party may terminate with 30 days notice."
    })
    assert response.status_code == 200
    body = response.json()
    assert body["review_id"] == "review-test-001"
    assert body["final_route"] in {"auto_approve", "human_review"}
    assert body["human_decision"] == "pending"
