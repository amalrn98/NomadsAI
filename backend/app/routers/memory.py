import logging
import os
import uuid
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from ..auth import bearer_scheme, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class MemoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    content: str = Field(default="", max_length=10000)
    destination: str = Field(min_length=1, max_length=160)
    image_url: HttpUrl | None = None
    mood: str | None = Field(default=None, max_length=32)
    weather: str | None = Field(default=None, max_length=32)
    companions: list[str] = Field(default_factory=list, max_length=20)


class MemoryResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    destination: str
    created_at: datetime
    image_url: str | None = None
    mood: str | None = None
    weather: str | None = None
    companions: list[str]


async def _supabase_request(
    method: str,
    access_token: str,
    *,
    params: dict[str, str] | None = None,
    payload: dict | None = None,
) -> list[dict]:
    base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    publishable_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
    if not base_url or not publishable_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account services are not configured.",
        )

    headers = {
        "apikey": publishable_key,
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.request(
                method,
                f"{base_url}/rest/v1/travel_memories",
                headers=headers,
                params=params,
                json=payload,
            )
    except httpx.HTTPError as exc:
        logger.warning("Supabase memory request failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Travel memory storage is temporarily unavailable.",
        ) from exc

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The sign-in session is invalid or expired.",
        )
    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Travel memory storage is temporarily unavailable.",
        )
    if not response.is_success:
        logger.warning("Supabase memory API returned HTTP %s", response.status_code)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The travel memory request could not be completed.",
        )
    if not response.content:
        return []
    data = response.json()
    return data if isinstance(data, list) else []


def _token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid sign-in session is required.",
        )
    return credentials.credentials


@router.get("/", response_model=list[MemoryResponse])
async def list_memories(
    user: Annotated[dict, Depends(get_current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
):
    return await _supabase_request(
        "GET",
        _token(credentials),
        params={
            "select": "id,title,content,destination,created_at,image_url,mood,weather,companions",
            "user_id": f"eq.{user['id']}",
            "order": "created_at.desc",
        },
    )


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    payload: MemoryCreate,
    user: Annotated[dict, Depends(get_current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
):
    rows = await _supabase_request(
        "POST",
        _token(credentials),
        payload={
            **payload.model_dump(mode="json"),
            "user_id": user["id"],
        },
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The travel memory could not be saved.",
        )
    return rows[0]


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: uuid.UUID,
    user: Annotated[dict, Depends(get_current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
):
    rows = await _supabase_request(
        "DELETE",
        _token(credentials),
        params={
            "id": f"eq.{memory_id}",
            "user_id": f"eq.{user['id']}",
            "select": "id",
        },
        payload=None,
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel memory not found.")
    return {"deleted": True}
