from fastapi import APIRouter, HTTPException, Request
from ..rate_limit import limiter
from typing import List
from ..models import TravelPlanRequest, TravelPlanResponse
from ..services.ai_itinerary import generate_dynamic_itinerary
from ..services.llm_provider import is_configured, get_ai_provider_info
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=TravelPlanResponse)
@limiter.limit("3/minute")
async def plan_travel(request: Request, payload: TravelPlanRequest):
    """
    Generate AI-powered travel itinerary with complete travel plan data.
    Uses dynamic AI generation without pre-fed data.
    """
    try:
        # Validate request
        if not payload.from_city or not payload.destination:
            raise HTTPException(status_code=400, detail="Both from_city and destination are required")
        
        if not payload.departure_date or not payload.return_date:
            raise HTTPException(status_code=400, detail="Both departure_date and return_date are required")
        
        # Calculate days
        from datetime import datetime
        start_date = datetime.strptime(payload.departure_date, "%Y-%m-%d")
        end_date = datetime.strptime(payload.return_date, "%Y-%m-%d")
        days = (end_date - start_date).days + 1
        
        if days < 1 or days > 90:
            raise HTTPException(status_code=400, detail="Trip duration must be between 1 and 90 days")
        
        if payload.travelers < 1 or payload.travelers > 20:
            raise HTTPException(status_code=400, detail="Number of travelers must be between 1 and 20")
        
        if not payload.interests:
            raise HTTPException(status_code=400, detail="At least one interest must be selected")
        
        # Generate dynamic AI itinerary
        logger.info(f"Generating dynamic AI itinerary for {payload.destination} ({days} days)")
        
        itinerary_data = await generate_dynamic_itinerary(
            destination=payload.destination,
            days=days,
            from_city=payload.from_city,
            budget=payload.budget,
            interests=payload.interests,
            travelers=payload.travelers,
            departure_date=payload.departure_date,
            return_date=payload.return_date
        )
        
        logger.info("Dynamic AI itinerary generated successfully")
        
        # Transform the AI response to match frontend expectations
        summary = itinerary_data.get("summary", f"Your {days}-day journey from {payload.from_city} to {payload.destination}")
        raw_itinerary = itinerary_data.get("itinerary", [])
        
        # Transform itinerary structure for frontend compatibility
        itinerary = []
        for day_data in raw_itinerary:
            transformed_day = {
                "day": day_data.get("day", 1),
                "title": day_data.get("theme", f"Day {day_data.get('day', 1)} in {payload.destination}"),
                "activities": day_data.get("activities", [])
            }
            itinerary.append(transformed_day)
        
        # Extract highlights from the first day or use defaults
        highlights = []
        if raw_itinerary and len(raw_itinerary) > 0:
            first_day = raw_itinerary[0]
            if "highlights" in first_day and isinstance(first_day["highlights"], list):
                highlights = first_day["highlights"]
        
        if not highlights:
            highlights = [f"Explore {payload.destination}", "Experience local culture", "Discover hidden gems"]
        
        # Extract other fields with proper string conversion
        cultural_insights = str(itinerary_data.get("cultural_insights", f"Immerse yourself in the rich culture of {payload.destination}"))
        local_recommendations = str(itinerary_data.get("local_recommendations", f"Discover authentic local experiences in {payload.destination}"))
        travel_tips = str(itinerary_data.get("travel_tips", f"Essential travel tips for visiting {payload.destination}"))
        estimated_budget = itinerary_data.get("estimated_budget", payload.budget)
        ai_provider = itinerary_data.get("ai_provider", "Dynamic AI Generation")
        
        return TravelPlanResponse(
            summary=summary,
            itinerary=itinerary,
            highlights=highlights,
            estimated_budget=estimated_budget,
            cultural_insights=cultural_insights,
            local_recommendations=local_recommendations,
            travel_tips=travel_tips,
            ai_provider=ai_provider,
            from_city=payload.from_city,
            destination=payload.destination,
            total_days=days
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate travel plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate travel plan: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check for the plan service"""
    return {
        "status": "healthy",
        "ai_configured": is_configured(),
        "ai_providers": get_ai_provider_info(),
        "service": "travel-planning"
    }