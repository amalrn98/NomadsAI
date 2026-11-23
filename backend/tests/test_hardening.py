import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app import rate_limit
from app.main import app
from app.services import emailer


def _request(headers=None, client=("10.0.0.9", 1234)):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "headers": raw, "client": client, "method": "GET", "path": "/"})


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in (
        "RATE_LIMIT_STORAGE_URI", "REDIS_URL", "RENDER", "APP_ENV", "ENVIRONMENT",
        "ALLOW_IN_MEMORY_RATE_LIMIT", "TRUSTED_PROXY_HOPS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_rate_limit_storage_defaults_to_memory_outside_production():
    assert rate_limit.resolve_storage_uri() == "memory://"


def test_rate_limit_storage_uses_redis_when_configured(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("RATE_LIMIT_STORAGE_URI", "rediss://example:6379")
    assert rate_limit.resolve_storage_uri() == "rediss://example:6379"


def test_rate_limit_fails_closed_in_production_without_redis(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    with pytest.raises(RuntimeError, match="Redis"):
        rate_limit.resolve_storage_uri()


def test_rate_limit_in_memory_in_production_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOW_IN_MEMORY_RATE_LIMIT", "true")
    assert rate_limit.resolve_storage_uri() == "memory://"


def test_client_key_ignores_forwarded_for_by_default():
    req = _request({"X-Forwarded-For": "1.2.3.4"})
    assert rate_limit.client_key(req) == "10.0.0.9"


def test_client_key_uses_trusted_hop_not_spoofable_leftmost(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "1")
    req = _request({"X-Forwarded-For": "6.6.6.6, 203.0.113.7"})
    assert rate_limit.client_key(req) == "203.0.113.7"


def test_client_key_falls_back_when_header_too_short(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "3")
    req = _request({"X-Forwarded-For": "203.0.113.7"})
    assert rate_limit.client_key(req) == "10.0.0.9"


def test_email_outbox_filename_never_contains_recipient(monkeypatch, tmp_path):
    monkeypatch.setenv("OUTBOX_DIR", str(tmp_path))
    emailer._write_outbox("a/../../etc/x@example.com", "s", "b")
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert "etc" not in files[0].name and "example" not in files[0].name
    assert "a/../../etc/x@example.com" in files[0].read_text()


def test_email_is_not_faked_in_production_without_smtp(monkeypatch, tmp_path):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("OUTBOX_DIR", str(tmp_path))
    monkeypatch.setattr(emailer, "SMTP_HOST", None)
    with pytest.raises(emailer.EmailNotConfiguredError):
        emailer.send_email("a@example.com", "s", "b")
    assert list(tmp_path.iterdir()) == []


def test_unauthenticated_pipeline_status_endpoint_is_gone():
    # It used to trigger a Gemini generation on every anonymous request.
    assert TestClient(app).get("/api/pipeline-status").status_code == 404
