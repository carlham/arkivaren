from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app


def test_health_ok_when_database_reachable():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_health_returns_503_when_database_unreachable():
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise ConnectionError("database unreachable")

    def broken_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    client = TestClient(app)
    response = client.get("/health")
    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
