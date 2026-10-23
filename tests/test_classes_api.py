from fastapi.testclient import TestClient
from server import app


def test_models_classes_endpoint():
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        res = client.get("/api/models/classes")
        assert res.status_code == 200
        data = res.json()
        assert "classes" in data
        assert data["count"] >= 80
        assert "person" in data["classes"]
        assert "car" in data["classes"]
        assert "motorcycle" in data["classes"]
