from fastapi.testclient import TestClient

from app.auth import get_current_user
from app.main import app
from app.routers import digest as digest_router

USER = {"id": "d8a2c13b-5e77-4f01-8c29-8e71f55b7a44", "email": "traveler@example.com", "email_confirmed_at": "2026-11-23T10:00:00Z"}


def _sign_in(user=USER):
    app.dependency_overrides[get_current_user] = lambda: user


def _sign_out():
    app.dependency_overrides.clear()


def test_digest_uses_live_news_and_excludes_sample_fixtures(monkeypatch):
    captured = {}
    sent = {}

    async def fake_get_signals(**kwargs):
        captured.update(kwargs)
        return [
            {
                "data_status": "sample",
                "title": "Stale sample flight",
                "source_url": None,
            },
            {
                "data_status": "live_search_result",
                "title": "Regional travel update",
                "source_name": "Example News",
                "snippet": "A source-linked update.",
                "source_url": "https://example.com/travel",
            },
        ]

    monkeypatch.setattr(digest_router, "get_signals", fake_get_signals)
    monkeypatch.setattr(
        digest_router,
        "send_email",
        lambda **kwargs: sent.update(kwargs),
    )

    _sign_in()
    try:
        response = TestClient(app).post(
            "/api/digest/send",
            json={"region": "Europe"},
        )
    finally:
        _sign_out()

    assert response.status_code == 200, response.text
    assert response.json() == {"sent": True, "included_items": 1}
    assert captured["destination"] == "Europe"
    assert captured["online_mode"] is True
    assert "Regional travel update" in sent["body"]
    assert "Stale sample flight" not in sent["body"]
    assert "https://example.com/travel" in sent["body"]
    assert sent["to"] == "traveler@example.com"


def test_digest_requires_sign_in():
    response = TestClient(app).post("/api/digest/send", json={"region": "Europe"})
    assert response.status_code == 401


def test_digest_ignores_client_supplied_recipient(monkeypatch):
    sent = {}

    async def fake_get_signals(**kwargs):
        return []

    monkeypatch.setattr(digest_router, "get_signals", fake_get_signals)
    monkeypatch.setattr(digest_router, "send_email", lambda **kwargs: sent.update(kwargs))

    _sign_in()
    try:
        response = TestClient(app).post(
            "/api/digest/send",
            json={"email": "victim@example.org", "region": "Asia"},
        )
    finally:
        _sign_out()

    assert response.status_code == 200, response.text
    assert sent["to"] == "traveler@example.com"


def test_digest_rejects_unverified_account_email():
    _sign_in({"id": USER["id"], "email": "traveler@example.com", "email_confirmed_at": None})
    try:
        response = TestClient(app).post("/api/digest/send", json={})
    finally:
        _sign_out()
    assert response.status_code == 400
