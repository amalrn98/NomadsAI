import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response

from ..rate_limit import limiter
from ..models import TravelPlanRequest, TravelPlanResponse
from ..services.ai_itinerary import generate_dynamic_itinerary
from ..services.llm_provider import is_configured, get_ai_provider_info

logger = logging.getLogger(__name__)
router = APIRouter()


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
        return TravelPlanResponse(
            summary=data["summary"],
            itinerary=[{"day": item["day"], "title": item["theme"], "activities": item["activities"]} for item in data["itinerary"]],
            highlights=data["itinerary"][0]["highlights"],
            estimated_budget=data["estimated_budget"],
            cultural_insights=data["cultural_insights"],
            local_recommendations=data["local_recommendations"],
            travel_tips=data["travel_tips"],
            ai_provider=data["ai_provider"],
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
