from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from ..rate_limit import limiter
from ..services.emailer import send_email
from .signals import get_signals

router = APIRouter()


class DigestRequest(BaseModel):
    email: EmailStr
    region: str | None = Field(default=None, max_length=80)


@router.post("/send")
@limiter.limit("3/hour")
async def send_digest(request: Request, req: DigestRequest):
    try:
        signals = await get_signals(destination=None, region=req.region, limit=5)
        items: List[str] = []
        for item in signals:
            if item["type"] == "event":
                items.append(f"Event: {item['name']} - {item['start_date']} in {item['location']}")
            elif item["type"] == "flight_deal":
                items.append(f"Flight deal: {item['from']} to {item['to']} for ${item['price']}")
            elif item["type"] == "hotel_rate":
                items.append(f"Hotel: {item['name']} in {item['city']} from ${item['price_per_night']}/night")

        send_email(
            to=str(req.email),
            subject="Nomad AI - Weekly Top Travel Opportunities",
            body="\n".join(items) or "No top signals this week.",
        )
        return {"sent": True}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The digest could not be sent. Please try again later.") from exc
