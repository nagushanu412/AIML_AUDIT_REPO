"""Integration tests for generic module API routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generic_module_metadata_requires_auth():
    response = client.get("/modules/JOURNAL_ENTRY_TESTING/metadata")
    assert response.status_code in (401, 403)


def test_generic_module_workspace_config_requires_auth():
    response = client.get("/modules/REVENUE_TESTING/workspace-config")
    assert response.status_code in (401, 403)


def test_module_catalog_still_public_with_auth_gate():
    response = client.get("/modules/catalog")
    assert response.status_code in (401, 403, 200)


def test_legacy_upload_route_exists():
    response = client.post("/upload")
    assert response.status_code in (401, 403, 422)


def test_legacy_revenue_route_exists():
    response = client.post("/revenue/run-rules")
    assert response.status_code in (401, 403, 422)


def test_legacy_procurement_route_exists():
    response = client.post("/procurement/run-rules")
    assert response.status_code in (401, 403, 422)


def test_openapi_includes_generic_modules():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    assert any("/modules/{module_code}/metadata" in p for p in paths)
    assert any("/modules/{module_code}/upload" in p for p in paths)
    assert any("/modules/{module_code}/run-rules" in p for p in paths)
