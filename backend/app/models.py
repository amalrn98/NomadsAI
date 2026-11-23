from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field
from pydantic import BaseModel, Field as PydanticField


class MemoryEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    destination: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class TravelPlanRequest(BaseModel):
    from_city: str = PydanticField(min_length=2, max_length=120)
    destination: str = PydanticField(min_length=2, max_length=120)
    departure_date: str = PydanticField(pattern=r"^\d{4}-\d{2}-\d{2}$")
    return_date: str = PydanticField(pattern=r"^\d{4}-\d{2}-\d{2}$")
    travelers: int = PydanticField(ge=1, le=20)
    budget: str = PydanticField(default="medium", max_length=32)
    interests: List[str] = PydanticField(min_length=1, max_length=10)


class TravelPlanResponse(BaseModel):
    summary: str
    itinerary: List[dict]
    highlights: List[str]
    estimated_budget: str
    cultural_insights: str
    local_recommendations: str
    travel_tips: str
    ai_provider: str
    from_city: str
    destination: str
    total_days: int
