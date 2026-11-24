import hashlib
import logging
import os
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from redis.exceptions import RedisError

from ..auth import get_current_user
from ..rate_limit import limiter
from ..runtime import is_production
from ..services.emailer import send_email
from .signals import get_signals

router = APIRouter()
logger = logging.getLogger(__name__)


async def _enforce_account_quota(user_id: str) -> None:
    """Apply a shared per-account digest quota using the configured Redis store."""
    redis_uri = (
        (os.getenv("RATE_LIMIT_STORAGE_URI") or os.getenv("REDIS_URL") or "").strip()
    )
    if not redis_uri:
        if is_production():
            raise HTTPException(
                status_code=503,
                detail="Digest delivery is temporarily unavailable.",
            )
        return

    try:
        client = Redis.from_url(redis_uri, decode_responses=True)
    except Exception as exc:
        logger.warning("Digest quota client could not be created: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Digest delivery is temporarily unavailable.",
        ) from exc

    try:
        key = f"nomadsai:digest:user:{user_id}:hour"
        count = await client.eval(
            "local count = redis.call('INCR', KEYS[1]); "
            "if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]); end; "
            "return count",
            1,
            key,
            3600,
        )
        if count > 3:
            account_ref = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
            logger.warning("Digest account quota exceeded (account_ref=%s)", account_ref)
            raise HTTPException(
                status_code=429,
                detail="Digest limit reached. Try again later.",
            )
    except RedisError as exc:
        logger.warning("Digest account quota store unavailable: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Digest delivery is temporarily unavailable.",
        ) from exc
    finally:
        try:
            await client.aclose()
        except Exception as exc:
            logger.debug("Digest quota client close failed: %s", type(exc).__name__)


class DigestRequest(BaseModel):
    """The recipient is never supplied by the client: the digest is only ever sent to
    the verified email of the signed-in account, so the endpoint cannot be used to
    send mail to third parties. A legacy `email` field in the body is ignored."""

    region: str | None = Field(default=None, max_length=80)


@router.post("/send")
@limiter.limit("3/hour")
async def send_digest(
    request: Request,
    response: Response,
    req: DigestRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    recipient = user.get("email")
    if not recipient:
        raise HTTPException(
            status_code=400,
            detail="Your account has no verified email address to send the digest to.",
        )
    await _enforce_account_quota(user["id"])
    try:
        # Search current, source-linked travel news. Local fixture data is filtered
        # out below and is never presented as a current opportunity.
        signals = await get_signals(
            request=request,
            response=response,
            destination=req.region or "global travel",
            region=req.region,
            limit=20,
            online_mode=True,
        )
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
            to=str(recipient),
            subject="Nomad AI - Travel News Digest",
            body=body,
        )
        return {"sent": True, "included_items": len(live_items)}
    except Exception as exc:
        logger.error("Digest send failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="The digest could not be sent. Please try again later.",
        ) from exc
