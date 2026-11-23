"""Validated AI itinerary generation.

Generation or parsing failures are raised to the API layer. This service never
returns a fabricated successful itinerary when the model call fails.
"""
import json
import logging
from typing import Any

from .llm_provider import generate_completion

logger = logging.getLogger(__name__)
_STRING_FIELDS = ("summary", "estimated_budget", "cultural_insights", "local_recommendations", "travel_tips")


def _clean_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid or missing itinerary field: {field}")
    return value.strip()


def _clean_string_list(value: Any, field: str, max_items: int = 12) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > max_items:
        raise ValueError(f"Invalid itinerary list: {field}")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must contain only non-empty strings.")
    return [item.strip() for item in value]


def _parse_json_object(response: str) -> dict[str, Any]:
    text = response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    if start < 0:
        raise ValueError("Gemini did not return a JSON object.")
    value, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(value, dict):
        raise ValueError("Gemini itinerary response must be a JSON object.")
    return value


def _validate_itinerary(data: dict[str, Any], destination: str, days: int, from_city: str, budget: str) -> dict[str, Any]:
    validated = {field: _clean_string(data.get(field), field) for field in _STRING_FIELDS}
    raw_days = data.get("itinerary")
    if not isinstance(raw_days, list) or len(raw_days) != days:
        raise ValueError(f"Expected exactly {days} itinerary days.")
    by_day: dict[int, dict[str, Any]] = {}
    for item in raw_days:
        if not isinstance(item, dict):
            raise ValueError("Each itinerary day must be an object.")
        number = item.get("day")
        if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= days:
            raise ValueError("Each itinerary day must have a valid day number.")
        if number in by_day:
            raise ValueError("Duplicate itinerary day number.")
        by_day[number] = item

    cleaned_days = []
    for number in range(1, days + 1):
        item = by_day.get(number)
        if item is None:
            raise ValueError(f"Missing itinerary day {number}.")
        cleaned_days.append({
            "day": number,
            "theme": _clean_string(item.get("theme"), f"day {number} theme"),
            "activities": _clean_string_list(item.get("activities"), f"day {number} activities"),
            "highlights": _clean_string_list(item.get("highlights"), f"day {number} highlights"),
            "cultural_insight": _clean_string(item.get("cultural_insight"), f"day {number} cultural_insight"),
            "local_secrets": _clean_string(item.get("local_secrets"), f"day {number} local_secrets"),
            "travel_tips": _clean_string(item.get("travel_tips"), f"day {number} travel_tips"),
        })
    validated.update({
        "itinerary": cleaned_days,
        "ai_provider": "Google Gemini",
        "from_city": from_city,
        "destination": destination,
        "total_days": days,
    })
    return validated


async def generate_dynamic_itinerary(
    destination: str,
    days: int,
    from_city: str = "various locations",
    budget: str = "medium",
    interests: list[str] | None = None,
    travelers: int = 1,
    departure_date: str | None = None,
    return_date: str | None = None,
) -> dict[str, Any]:
    interests = interests or ["culture", "food", "sightseeing"]
    prompt = f"""Create a practical {days}-day travel itinerary.
Origin: {from_city}
Destination: {destination}
Dates: {departure_date or "not specified"} to {return_date or "not specified"}
Travelers: {travelers}
Budget tier: {budget}
Interests: {", ".join(interests)}

Return only a JSON object with keys summary, itinerary, estimated_budget, cultural_insights,
local_recommendations, travel_tips. itinerary must contain exactly {days} objects numbered
1 through {days}. Each day object must contain day (integer), theme (string), activities
(array of strings), highlights (array of strings), cultural_insight (string), local_secrets
(string), and travel_tips (string). Do not invent current prices, opening hours, availability,
or transport schedules. Mark details requiring current verification as estimates. Avoid
fabricated addresses or venue claims."""
    messages = [
        {"role": "system", "content": "You are a careful travel planner. Return valid JSON only."},
        {"role": "user", "content": prompt},
    ]
    try:
        response = await generate_completion(messages, temperature=0.5, max_output_tokens=min(7000, 500 * days))
        return _validate_itinerary(_parse_json_object(response), destination, days, from_city, budget)
    except Exception:
        logger.exception("Itinerary generation or validation failed for destination %s", destination)
        raise
