"""Wave 0 Milestone 4 — API integration tests (require live database)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.database import validate_database_connection
from app.main import app

client = TestClient(app)


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "AIML" in body["service"]


@requires_db
def test_demo_login_returns_token():
    response = client.post(
        "/auth/login",
        json={"email": "auditor@demo.auditai.com", "password": "AuditAI2026!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body.get("organization_id") is not None


@requires_db
def test_authenticated_clients_list():
    login = client.post(
        "/auth/login",
        json={"email": "auditor@demo.auditai.com", "password": "AuditAI2026!"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/clients",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@requires_db
def test_unauthenticated_clients_rejected():
    response = client.get("/clients")
    assert response.status_code == 401
