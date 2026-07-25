"""Remediation M1 follow-up — clients.organization_id NOT NULL + isolation."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, validate_database_connection
from app.main import app
from app.models.audit import User
from app.models.organization_id_events import register_organization_id_listeners

register_organization_id_listeners()

client = TestClient(app)


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


@requires_db
def test_clients_organization_id_null_rejected_at_database():
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.default_organization_id.isnot(None))
            .order_by(User.created_at.desc())
            .first()
        )
        if user is None:
            pytest.skip("No user available for clients.organization_id constraint test")

        with pytest.raises(IntegrityError):
            db.execute(
                text(
                    """
                    INSERT INTO clients (
                        id, user_id, organization_id, name, status
                    )
                    VALUES (
                        :id, :user_id, NULL, 'NULL-ORG-CLIENT-TEST', 'active'
                    )
                    """
                ),
                {"id": str(uuid.uuid4()), "user_id": str(user.id)},
            )
            db.commit()
        db.rollback()
    finally:
        db.close()


@requires_db
def test_clients_organization_id_is_not_null_in_database():
    db = SessionLocal()
    try:
        nulls = db.execute(
            text("SELECT count(*) FROM clients WHERE organization_id IS NULL")
        ).scalar()
        nullable = db.execute(
            text(
                """
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = 'clients' AND column_name = 'organization_id'
                """
            )
        ).scalar()
        assert int(nulls or 0) == 0
        assert nullable == "NO"
    finally:
        db.close()


@requires_db
def test_clients_api_cross_tenant_isolation():
    """Firm B cannot read/update/delete Firm A's client via HTTP."""
    suffix = uuid.uuid4().hex[:10]
    reg_a = client.post(
        "/auth/register",
        json={
            "email": f"clients-a-{suffix}@example.com",
            "password": "ClientsIsoA2026!",
            "full_name": "Clients Firm A",
            "company_name": f"Clients Firm A {suffix}",
        },
    )
    assert reg_a.status_code == 201, reg_a.text
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    reg_b = client.post(
        "/auth/register",
        json={
            "email": f"clients-b-{suffix}@example.com",
            "password": "ClientsIsoB2026!",
            "full_name": "Clients Firm B",
            "company_name": f"Clients Firm B {suffix}",
        },
    )
    assert reg_b.status_code == 201, reg_b.text
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    created = client.post(
        "/clients",
        headers=headers_a,
        json={"name": f"Client A {suffix}", "industry": "Services"},
    )
    assert created.status_code == 201, created.text
    client_id = created.json()["id"]

    for method, path, kwargs in (
        ("GET", f"/clients/{client_id}", {}),
        ("PATCH", f"/clients/{client_id}", {"json": {"name": "Hijack"}}),
        ("DELETE", f"/clients/{client_id}", {}),
    ):
        response = client.request(method, path, headers=headers_b, **kwargs)
        assert response.status_code in (403, 404), (
            f"{method} {path} expected 403/404, got {response.status_code}: {response.text}"
        )

    listed = client.get("/clients", headers=headers_b)
    assert listed.status_code == 200
    assert client_id not in {str(row["id"]) for row in listed.json()}

    own = client.get(f"/clients/{client_id}", headers=headers_a)
    assert own.status_code == 200
