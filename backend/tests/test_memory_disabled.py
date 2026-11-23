from app.main import app


def test_persistent_memory_routes_are_not_exposed():
    paths = set(app.openapi()["paths"])
    assert not any(path.startswith("/api/memory") for path in paths)


def test_chat_agent_has_no_unauthenticated_memory_store():
    from app.services.ai_agent import ai_agent

    assert not hasattr(ai_agent, "memory_store")
    assert not hasattr(ai_agent, "update_user_memory")
