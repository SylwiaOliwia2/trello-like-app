import pytest
from fastapi.testclient import TestClient


@pytest.mark.smoke
@pytest.mark.API
def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
