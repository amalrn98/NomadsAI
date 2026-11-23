from fastapi.testclient import TestClient

from app.main import app
from app.routers import digest as digest_router


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

    response = TestClient(app).post(
        "/api/digest/send",
        json={"email": "traveler@example.com", "region": "Europe"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"sent": True, "included_items": 1}
    assert captured["destination"] == "Europe"
    assert captured["online_mode"] is True
    assert "Regional travel update" in sent["body"]
    assert "Stale sample flight" not in sent["body"]
    assert "https://example.com/travel" in sent["body"]
