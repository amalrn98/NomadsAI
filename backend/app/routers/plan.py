import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response

from ..rate_limit import limiter
from ..models import TravelPlanRequest, TravelPlanResponse
from ..services.ai_itinerary import generate_dynamic_itinerary
from ..services.llm_provider import is_configured, get_ai_provider_info

logger = logging.getLogger(__name__)
router = APIRouter()


def _activity_text(value):
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        title = value.get("title") or value.get("name")
        description = value.get("description")
        if isinstance(title, str) and title.strip():
            return f"{title.strip()}: {description.strip()}" if isinstance(description, str) and description.strip() else title.strip()
    raise ValueError("Each itinerary activity must contain readable text.")


@router.post("/", response_model=TravelPlanResponse)
@limiter.limit("3/minute")
async def plan_travel(request: Request, response: Response, payload: TravelPlanRequest):
    try:
        try:
            start_date = datetime.strptime(payload.departure_date, "%Y-%m-%d")
            end_date = datetime.strptime(payload.return_date, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Dates must be valid calendar dates in YYYY-MM-DD format.") from exc

        days = (end_date - start_date).days + 1
        if not 1 <= days <= 90:
            raise HTTPException(status_code=400, detail="Trip duration must be between 1 and 90 days.")
        if not payload.interests:
            raise HTTPException(status_code=400, detail="At least one interest must be selected.")

        data = await generate_dynamic_itinerary(
            destination=payload.destination,
            days=days,
            from_city=payload.from_city,
            budget=payload.budget,
            interests=payload.interests,
            travelers=payload.travelers,
            departure_date=payload.departure_date,
            return_date=payload.return_date,
        )
        raw_days = data.get("itinerary")
        if not isinstance(raw_days, list) or len(raw_days) != days:
            raise ValueError("The itinerary response does not contain the requested number of days.")
        itinerary = []
        for item in raw_days:
            if not isinstance(item, dict):
                raise ValueError("Invalid itinerary day.")
            activities = item.get("activities")
            if not isinstance(activities, list) or not activities:
                raise ValueError("An itinerary day has no valid activities.")
            itinerary.append({
                "day": item.get("day"),
                "title": item.get("theme") or item.get("title"),
                "activities": [_activity_text(activity) for activity in activities],
            })

        first_day = raw_days[0]
        highlights = data.get("highlights") or first_day.get("highlights")
        if not isinstance(highlights, list) or not highlights or any(not isinstance(item, str) for item in highlights):
            raise ValueError("The itinerary response has no valid highlights.")

        return TravelPlanResponse(
            summary=data["summary"],
            itinerary=itinerary,
            highlights=highlights,
            estimated_budget=data["estimated_budget"],
            cultural_insights=data["cultural_insights"],
            local_recommendations=data["local_recommendations"],
            travel_tips=data["travel_tips"],
            ai_provider=data.get("ai_provider", "Google Gemini"),
            from_city=payload.from_city,
            destination=payload.destination,
            total_days=days,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Travel plan generation failed")
        raise HTTPException(status_code=502, detail="The itinerary service could not generate a valid plan. Please retry.") from exc


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ai_configured": is_configured(),
        "ai_providers": get_ai_provider_info(),
        "service": "travel-planning",
    }
