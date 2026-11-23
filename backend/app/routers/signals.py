from datetime import datetime, timezone
from typing import List, Optional
import asyncio
import json
import os

from fastapi import APIRouter, Query, Request, Response

from ..rate_limit import limiter
from ..services.web_search import search_news

router = APIRouter()
MOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data")


def _load_json(filename: str):
    path = os.path.abspath(os.path.join(MOCK_DIR, filename))
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


@router.get("/")
@limiter.limit("30/minute")
async def get_signals(
    request: Request,
    response: Response,
    destination: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    online_mode: bool = False,
):
    events = _load_json("events.json")
    flights = _load_json("flights.json")
    hotels = _load_json("hotels.json")
    results: List[dict] = []

    for event in events:
        if destination and destination.lower() not in event["location"].lower():
            continue
        if region and event.get("region") != region:
            continue
        results.append({"type": "event", **event})

    for flight in flights:
        if destination and destination.lower() not in flight["to"].lower():
            continue
        if region and flight.get("region") != region:
            continue
        results.append({"type": "flight_deal", **flight})

    for hotel in hotels:
        if destination and destination.lower() not in hotel["city"].lower():
            continue
        if region and hotel.get("region") != region:
            continue
        results.append({"type": "hotel_rate", **hotel})

    if online_mode and destination:
        query = f"{destination} travel events festival {datetime.now(timezone.utc).year}"
        for news_item in await asyncio.to_thread(search_news, query, max_results=5):
            results.append({"type": "news", **news_item})

    today = datetime.now(timezone.utc).date()
    filtered: List[dict] = []
    for item in results:
        if item.get("type") in {"event", "news"}:
            date_str = item.get("start_date") or item.get("date")
            if date_str:
                try:
                    if datetime.fromisoformat(date_str).date() < today:
                        continue
                except (TypeError, ValueError):
                    continue
        filtered.append(item)

    def sort_key(item):
        date_str = item.get("date") or item.get("start_date") or item.get("found_at")
        if date_str:
            try:
                normalized = date_str.replace("Z", "+00:00")
                return datetime.fromisoformat(normalized).timestamp()
            except (AttributeError, TypeError, ValueError, OverflowError):
                pass
        return 0.0

    filtered.sort(key=sort_key, reverse=True)
    return filtered[:limit]
