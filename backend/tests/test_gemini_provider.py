from app.services.llm_provider import GeminiProvider, _messages_to_gemini


def test_messages_convert_system_and_roles():
    instruction, contents = _messages_to_gemini([
        {"role": "system", "content": "You are a travel planner."},
        {"role": "user", "content": "Plan a trip."},
        {"role": "assistant", "content": "Where to?"},
        {"role": "user", "content": "Kyoto."},
    ])

    assert instruction == {"parts": [{"text": "You are a travel planner."}]}
    assert contents == [
        {"role": "user", "parts": [{"text": "Plan a trip."}]},
        {"role": "model", "parts": [{"text": "Where to?"}]},
        {"role": "user", "parts": [{"text": "Kyoto."}]},
    ]


def test_adjacent_same_role_messages_are_combined():
    _, contents = _messages_to_gemini([
        {"role": "user", "content": "First part."},
        {"role": "user", "content": "Second part."},
    ])
    assert len(contents) == 1
    assert contents[0]["parts"] == [
        {"text": "First part."},
        {"text": "Second part."},
    ]


def test_gemini_configuration_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")

    provider = GeminiProvider()

    assert provider.is_configured()
    assert provider.model == "gemini-test-model"


def test_missing_gemini_key_is_not_configured(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert not GeminiProvider().is_configured()
