import pytest
from pydantic import ValidationError

from app.routers.chat import ChatMessage, ChatRequest
from app.services.ai_itinerary import _validate_itinerary


def test_chat_accepts_frontend_travel_context_and_resolves_destination():
    request = ChatRequest(
        messages=[ChatMessage(role="user", content="What should I see?")],
        travel_context={"destination": "Kyoto", "travelers": 2},
    )
    assert request.resolved_destination() == "Kyoto"


def test_chat_rejects_oversized_combined_message_content():
    with pytest.raises(ValidationError):
        ChatRequest(messages=[
            ChatMessage(role="user", content="x" * 8000),
            ChatMessage(role="assistant", content="y" * 8000),
            ChatMessage(role="user", content="z" * 8000),
            ChatMessage(role="assistant", content="a" * 1000),
        ])


def test_itinerary_rejects_non_string_activities():
    data = {
        "summary": "A trip",
        "estimated_budget": "Medium",
        "cultural_insights": "Insight",
        "local_recommendations": "Recommendations",
        "travel_tips": "Tips",
        "itinerary": [{
            "day": 1,
            "theme": "Old town",
            "activities": [{"name": "Temple"}],
            "highlights": ["Temple"],
            "cultural_insight": "Insight",
            "local_secrets": "Secret",
            "travel_tips": "Tip",
        }],
    }
    with pytest.raises(ValueError):
        _validate_itinerary(data, "Kyoto", 1, "Osaka", "medium")
