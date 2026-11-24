import asyncio

import pytest
from fastapi import HTTPException
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
    _sign_in({"id": USER["id"], "email": None})
    try:
        response = TestClient(app).post("/api/digest/send", json={})
    finally:
        _sign_out()
    assert response.status_code == 400



def test_digest_account_quota_is_shared_and_limited(monkeypatch):
    class FakeRedisClient:
        def __init__(self):
            self.count = 0
            self.expirations = []
            self.closed = False

        async def eval(self, script, numkeys, key, seconds):
            assert numkeys == 1
            assert "INCR" in script and "EXPIRE" in script
            self.count += 1
            if self.count == 1:
                self.expirations.append((key, seconds))
            return self.count

        async def aclose(self):
            self.closed = True

    fake = FakeRedisClient()

    class FakeRedis:
        @classmethod
        def from_url(cls, uri, decode_responses=True):
            assert uri == "redis://test"
            return fake

    monkeypatch.setenv("RATE_LIMIT_STORAGE_URI", "redis://test")
    monkeypatch.setattr(digest_router, "Redis", FakeRedis)

    async def run():
        for _ in range(3):
            await digest_router._enforce_account_quota(USER["id"])
        with pytest.raises(HTTPException) as exc:
            await digest_router._enforce_account_quota(USER["id"])
        return exc.value.status_code

    assert asyncio.run(run()) == 429
    assert fake.expirations == [(f"nomadsai:digest:user:{USER['id']}:hour", 3600)]
    assert fake.closed is True


def test_digest_account_quota_fails_closed_in_production_without_redis(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("RATE_LIMIT_STORAGE_URI", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    async def run():
        with pytest.raises(HTTPException) as exc:
            await digest_router._enforce_account_quota(USER["id"])
        return exc.value.status_code

    assert asyncio.run(run()) == 503



def test_digest_failure_logs_do_not_expose_provider_details(monkeypatch, caplog):
    async def fake_get_signals(**kwargs):
        return [{
            "data_status": "live_search_result",
            "title": "Travel update",
            "snippet": "A travel update.",
            "source_url": "https://example.com/travel",
        }]

    def fail_send(**kwargs):
        raise RuntimeError("SMTP_PASS=private-provider-secret")

    monkeypatch.setattr(digest_router, "get_signals", fake_get_signals)
    monkeypatch.setattr(digest_router, "send_email", fail_send)
    _sign_in()
    try:
        response = TestClient(app, client=("203.0.113.77", 1234)).post("/api/digest/send", json={})
    finally:
        _sign_out()

    assert response.status_code == 502
    assert "private-provider-secret" not in caplog.text
    assert "SMTP_PASS" not in caplog.text
    assert "RuntimeError" in caplog.text
