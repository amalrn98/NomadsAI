from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


def test_readiness_reports_missing_production_configuration(monkeypatch):
    for name in (
        "GEMINI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "RATE_LIMIT_STORAGE_URI",
        "REDIS_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    response = TestClient(app).get("/readyz")

    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "not_ready"


def test_readiness_passes_when_required_services_are_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "test-publishable-key")
    monkeypatch.setenv("RATE_LIMIT_STORAGE_URI", "rediss://example:6379")

    response = TestClient(app).get("/readyz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"gemini": True, "supabase": True, "redis": True},
    }


def test_production_smoke_endpoint_is_hidden_without_valid_token(monkeypatch):
    monkeypatch.setenv("SMOKE_TEST_TOKEN", "expected-secret")

    response = TestClient(app).post("/internal/smoke/gemini")

    assert response.status_code == 404


def test_production_smoke_endpoint_checks_generation_and_streaming(monkeypatch):
    monkeypatch.setenv("SMOKE_TEST_TOKEN", "expected-secret")
    calls = {"generation": 0, "streaming": 0}

    async def fake_generate(messages, **kwargs):
        calls["generation"] += 1
        assert kwargs["max_output_tokens"] == 16
        return "NOMADSAI_SMOKE_OK"

    async def fake_stream(messages, **kwargs):
        calls["streaming"] += 1
        yield "NOMADSAI_SMOKE_OK"

    monkeypatch.setattr(main_module, "generate_completion", fake_generate)
    monkeypatch.setattr(main_module, "stream_completion", fake_stream)

    response = TestClient(app).post(
        "/internal/smoke/gemini",
        headers={"X-Smoke-Test-Token": "expected-secret"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "ok",
        "generation": "ok",
        "streaming": "ok",
    }
    assert calls == {"generation": 1, "streaming": 1}
