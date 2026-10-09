# tests/M6/test_api.py

from fastapi.testclient import TestClient
from capstone.M6.main import app

# Create an in-process HTTP test client.
client = TestClient(app)


def test_health_endpoint():
    # Check the API without accessing contract fixtures.
    response = client.get("/health")

    # Validate the HTTP response.
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_contract_returns_404():
    # Request a deliberately nonexistent contract.
    response = client.post(
        "/reviews",
        json={"contract_id": "DOES-NOT-EXIST-000"},
    )

    # Verify that unknown contracts are rejected.
    assert response.status_code == 404