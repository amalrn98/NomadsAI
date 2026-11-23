from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from ..rate_limit import limiter
from ..services.gpt_oss import generate_itinerary
from ..services.llm_client import is_configured

router = APIRouter()


class TravelPlanRequest(BaseModel):
    from_city: str = Field(min_length=2, max_length=120)
    destination: str = Field(min_length=2, max_length=120)
    days: int = Field(ge=1, le=90)
    budget: Optional[str] = Field(default="premium", max_length=32)
    interests: Optional[List[str]] = Field(default_factory=lambda: ["business", "culture"], max_length=10)
    travelers: Optional[int] = Field(default=1, ge=1, le=20)
    departure_date: Optional[str] = None
    return_date: Optional[str] = None


class TravelPlanResponse(BaseModel):
    itinerary: dict
    ai_enhanced: bool
    ai_provider: str
    from_city: str
    destination: str
    total_days: int
    estimated_budget: str


@router.post("/plan", response_model=TravelPlanResponse)
@limiter.limit("3/minute")
async def plan_travel(request: Request, response: Response, payload: TravelPlanRequest):
    try:
        data = await generate_itinerary(
            destination=payload.destination,
            days=payload.days,
            budget=payload.budget,
            interests=payload.interests,
            travel_month=None,
            from_city=payload.from_city,
            travelers=payload.travelers,
        )
        return TravelPlanResponse(
            itinerary=data,
            ai_enhanced=bool(data.get("ai_enhanced", False)),
            ai_provider=data.get("ai_provider", "legacy"),
            from_city=payload.from_city,
            destination=payload.destination,
            total_days=payload.days,
            estimated_budget=data.get("estimated_budget", payload.budget),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The legacy itinerary service failed. Please use /api/plan.") from exc


@router.get("/surprise")
async def get_surprise_destinations():
    return {"suggestions": [
        "Chefchaouen, Morocco",
        "Tbilisi, Georgia",
        "Varanasi, India",
        "Patagonia, Chile",
        "Medellin, Colombia",
    ]}


@router.get("/destinations")
async def get_available_destinations():
    return {"destinations": [
        {"name": "New York", "country": "United States", "code": "NYC", "category": "business"},
        {"name": "London", "country": "United Kingdom", "code": "LON", "category": "business"},
        {"name": "Tokyo", "country": "Japan", "code": "TYO", "category": "business"},
        {"name": "Paris", "country": "France", "code": "PAR", "category": "culture"},
        {"name": "Barcelona", "country": "Spain", "code": "BCN", "category": "culture"},
        {"name": "Singapore", "country": "Singapore", "code": "SIN", "category": "business"},
        {"name": "Dubai", "country": "UAE", "code": "DXB", "category": "business"},
        {"name": "Bangkok", "country": "Thailand", "code": "BKK", "category": "culture"},
        {"name": "Mexico City", "country": "Mexico", "code": "MEX", "category": "culture"},
        {"name": "Cape Town", "country": "South Africa", "code": "CPT", "category": "leisure"},
    ]}
