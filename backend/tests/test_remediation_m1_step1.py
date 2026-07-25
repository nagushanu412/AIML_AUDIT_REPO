"""Remediation Milestone 1 Step 1 — engagement.organization_id NOT NULL."""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, validate_database_connection
from app.models.audit import AuditEngagement, AuditProject, Client
from app.services.project_access import get_owned_project


def _db_available() -> bool:
    try:
        validate_database_connection()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(not _db_available(), reason="PostgreSQL not available")


def test_get_owned_project_uses_engagement_organization_id_not_client():
    """Access must follow engagement.organization_id, not clients.organization_id."""
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    tenant = MagicMock()
    tenant.user = user
    tenant.organization_id = org_a

    client = Client(
        id=uuid.uuid4(),
        name="Cross-tenant client",
        user_id=user.id,
        organization_id=org_b,  # deliberately different from engagement
    )
    engagement = AuditEngagement(
        id=uuid.uuid4(),
        client_id=client.id,
        client=client,
        organization_id=org_a,
        financial_year="FY 2026-27",
        financial_year_end=date(2027, 3, 31),
    )
    project = AuditProject(
        id=uuid.uuid4(),
        engagement_id=engagement.id,
        engagement=engagement,
        name="Journal Testing",
        project_type="journal_testing",
    )

    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.options.return_value = query
    query.filter.return_value = query
    query.first.return_value = project

    owned = get_owned_project(db, project.id, tenant)
    assert owned.id == project.id

    tenant.organization_id = org_b
    with pytest.raises(HTTPException) as exc:
        get_owned_project(db, project.id, tenant)
    assert exc.value.status_code == 403


@requires_db
def test_engagement_organization_id_null_rejected_at_database():
    """Null organization_id must fail at the DB constraint, not only in app code."""
    db = SessionLocal()
    try:
        client = (
            db.query(Client)
            .filter(Client.organization_id.isnot(None))
            .order_by(Client.created_at.desc())
            .first()
        )
        if client is None:
            pytest.skip("No client with organization_id available for constraint test")

        with pytest.raises(IntegrityError):
            db.execute(
                text(
                    """
                    INSERT INTO audit_engagements (
                        id, client_id, organization_id, financial_year, audit_type,
                        status, financial_year_end, large_value_threshold
                    )
                    VALUES (
                        :id, :client_id, NULL, 'FY NULL-ORG-TEST', 'Statutory',
                        'planned', :fy_end, 100000
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "client_id": str(client.id),
                    "fy_end": date(2027, 3, 31),
                },
            )
            db.commit()
        db.rollback()
    finally:
        db.close()
