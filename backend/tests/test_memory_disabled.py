from fastapi.testclient import TestClient

from app.main import app


def test_persistent_memory_routes_are_mounted_and_require_authentication():
    client = TestClient(app)
    response = client.get("/api/memory/")
    assert response.status_code == 401


def test_chat_agent_does_not_keep_unscoped_process_memory():
    from app.services.ai_agent import ai_agent

    assert not hasattr(ai_agent, "memory_store")
    assert not hasattr(ai_agent, "update_user_memory")
