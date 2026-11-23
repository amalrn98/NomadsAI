from typing import List

from fastapi import APIRouter, HTTPException, Request, Response
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
async def send_digest(request: Request, response: Response, req: DigestRequest):
    try:
        signals = await get_signals(
            request=request,
            response=response,
            destination=None,
            region=req.region,
            limit=20,
            online_mode=False,
        )
        # Local JSON fixtures are sample data, never current travel deals.
        # Only source-linked live search results may be included in a digest.
        live_items = [
            item for item in signals
            if item.get("data_status") == "live_search_result"
            and item.get("source_url")
        ]
        items: List[str] = []
        for item in live_items:
            title = item.get("title")
            source = item.get("source_name")
            snippet = item.get("snippet")
            url = item.get("source_url")
            if title:
                items.append(f"News: {title}")
                if source:
                    items.append(f"Source: {source}")
                if snippet:
                    items.append(snippet)
                items.append(f"Verify details: {url}")

        body = "\n".join(items) or (
            "No source-linked live travel news was available. "
            "Sample flight and hotel fixtures are intentionally excluded."
        )
        send_email(
            to=str(req.email),
            subject="Nomad AI - Travel News Digest",
            body=body,
        )
        return {"sent": True, "included_items": len(live_items)}
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="The digest could not be sent. Please try again later.",
        ) from exc
