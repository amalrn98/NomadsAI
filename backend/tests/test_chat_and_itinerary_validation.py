import asyncio
import json

import pytest
from pydantic import ValidationError

from app.routers.chat import ChatMessage, ChatRequest
from app.services import ai_itinerary
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



def test_itinerary_uses_search_context_and_marks_it_unverified(monkeypatch):
    captured = {}

    async def fake_search(query, max_results=5):
        assert "Kyoto" in query
        assert max_results == 5
        return [
            {
                "title": "Official visitor guide",
                "href": "https://example.com/kyoto",
                "snippet": "Visitor information and cultural sites.",
            },
            {
                "title": "Unsafe result",
                "href": "javascript:alert(1)",
                "snippet": "Not a valid source URL.",
            },
        ]

    async def fake_generate(messages, **kwargs):
        captured["prompt"] = messages[-1]["content"]
        return json.dumps({
            "summary": "A one-day Kyoto plan",
            "estimated_budget": "Medium",
            "cultural_insights": "Respect local customs.",
            "local_recommendations": "Explore local streets.",
            "travel_tips": "Check official transit information.",
            "itinerary": [{
                "day": 1,
                "theme": "Historic Kyoto",
                "activities": ["Visit a temple"],
                "highlights": ["Temple visit"],
                "cultural_insight": "Be respectful.",
                "local_secrets": "Explore side streets.",
                "travel_tips": "Verify opening times.",
            }],
        })

    monkeypatch.setattr(ai_itinerary, "search_web", fake_search)
    monkeypatch.setattr(ai_itinerary, "generate_completion", fake_generate)

    async def run():
        return await ai_itinerary.generate_dynamic_itinerary(
            destination="Kyoto",
            days=1,
            from_city="Osaka",
            budget="medium",
            interests=["culture"],
        )

    result = asyncio.run(run())
    assert "unverified reference material" in captured["prompt"]
    assert result["verified"] is False
    assert result["data_status"] == "ai_generated_with_unverified_search_context"
    assert result["sources"] == [{
        "title": "Official visitor guide",
        "url": "https://example.com/kyoto",
        "snippet": "Visitor information and cultural sites.",
    }]
    assert result["retrieved_at"]
