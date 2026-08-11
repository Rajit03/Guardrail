from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Verify health check returns status ok and service name."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "guardrail-api"
