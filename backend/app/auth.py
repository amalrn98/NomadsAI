import os
import uuid

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


def _supabase_config() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account services are not configured.",
        )
    return url, key


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str | None]:
    """Validate a Supabase access token with Auth, never trust client-supplied IDs."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid sign-in session is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    base_url, publishable_key = _supabase_config()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0)) as client:
            response = await client.get(
                f"{base_url}/auth/v1/user",
                headers={
                    "apikey": publishable_key,
                    "Authorization": f"Bearer {credentials.credentials}",
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The account service is temporarily unavailable.",
        ) from exc

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The sign-in session is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The account service could not validate the session.",
        )

    try:
        user = response.json()
        user_id = str(uuid.UUID(str(user["id"])))
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The account service returned an invalid identity.",
        ) from exc

    return {"id": user_id, "email": _verified_email(user)}


def _verified_email(user: dict) -> str | None:
    """Return an account email only after Supabase confirms it."""
    email = user.get("email")
    confirmed_at = user.get("email_confirmed_at") or user.get("confirmed_at")
    if not isinstance(email, str) or not email.strip() or not confirmed_at:
        return None
    return email.strip()
