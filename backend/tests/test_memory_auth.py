import uuid

from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import get_current_user
from app.main import app
from app.routers import memory as memory_router
from app.auth import bearer_scheme

USER_ID = "d8a2c13b-5e77-4f01-8c29-8e71f55b7a44"
OTHER_USER_ID = "b2d2a1e4-42f5-4a65-9d82-2c3f42c1a812"


def _auth_overrides():
    app.dependency_overrides[get_current_user] = lambda: {"id": USER_ID, "email": "user@example.test"}
    app.dependency_overrides[bearer_scheme] = lambda: HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="test-access-token"
    )


def _clear_overrides():
    app.dependency_overrides.clear()


def test_memory_routes_require_a_valid_bearer_session():
    response = TestClient(app).get("/api/memory/")
    assert response.status_code == 401


def test_memory_create_uses_verified_subject_not_client_identity(monkeypatch):
    captured = {}

    async def fake_request(method, token, *, params=None, payload=None):
        captured.update(method=method, token=token, payload=payload, params=params)
        return [{
            "id": str(uuid.uuid4()),
            "title": "First trip",
            "content": "A story",
            "destination": "Kochi",
            "created_at": "2026-11-23T10:00:00Z",
            "image_url": None,
            "mood": None,
            "weather": None,
            "companions": [],
        }]

    monkeypatch.setattr(memory_router, "_supabase_request", fake_request)
    _auth_overrides()
    try:
        response = TestClient(app).post(
            "/api/memory/",
            headers={"Authorization": "Bearer test-access-token"},
            json={"title": "First trip", "content": "A story", "destination": "Kochi"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 201, response.text
    assert captured["method"] == "POST"
    assert captured["token"] == "test-access-token"
    assert captured["payload"]["user_id"] == USER_ID
    assert captured["payload"]["user_id"] != OTHER_USER_ID


def test_memory_list_is_filtered_to_verified_subject(monkeypatch):
    captured = {}

    async def fake_request(method, token, *, params=None, payload=None):
        captured.update(method=method, token=token, params=params)
        return []

    monkeypatch.setattr(memory_router, "_supabase_request", fake_request)
    _auth_overrides()
    try:
        response = TestClient(app).get(
            "/api/memory/",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert captured["params"]["user_id"] == f"eq.{USER_ID}"
    assert captured["token"] == "test-access-token"


def test_memory_delete_filters_by_verified_subject_and_returns_404_for_no_match(monkeypatch):
    captured = {}

    async def fake_request(method, token, *, params=None, payload=None):
        captured.update(method=method, token=token, params=params)
        return []

    monkeypatch.setattr(memory_router, "_supabase_request", fake_request)
    memory_id = str(uuid.uuid4())
    _auth_overrides()
    try:
        response = TestClient(app).delete(
            f"/api/memory/{memory_id}",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert captured["method"] == "DELETE"
    assert captured["params"]["id"] == f"eq.{memory_id}"
    assert captured["params"]["user_id"] == f"eq.{USER_ID}"
