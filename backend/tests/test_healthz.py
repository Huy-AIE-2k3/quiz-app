from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "MATHRIX"
    assert "timestamp" in data


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "MATHRIX API Engine" in data["message"]
