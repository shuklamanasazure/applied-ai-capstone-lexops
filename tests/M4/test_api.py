"""API contract tests that do not need to download embedding models."""

from fastapi.testclient import TestClient  # Exercise the API in-process.
from lexops_m4.main import app  # Import app without triggering startup.


def test_health_before_startup_reports_not_loaded():
    """Readiness endpoint should clearly report whether startup built the index."""

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "index_loaded" in response.json()
