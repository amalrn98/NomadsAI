"""Shared rate limiter for public, cost-bearing API endpoints."""

import ipaddress
import logging
import os

from dotenv import load_dotenv
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .runtime import env_flag, is_production

load_dotenv()

logger = logging.getLogger(__name__)


def resolve_storage_uri() -> str:
    """Pick the limiter storage backend.

    Redis (RATE_LIMIT_STORAGE_URI or REDIS_URL) is required in production so limits
    are shared across instances and survive restarts. Production without Redis fails
    closed at startup unless ALLOW_IN_MEMORY_RATE_LIMIT=true is set deliberately.
    """
    uri = (os.getenv("RATE_LIMIT_STORAGE_URI") or os.getenv("REDIS_URL") or "").strip()
    if uri:
        return uri
    if is_production() and not env_flag("ALLOW_IN_MEMORY_RATE_LIMIT"):
        raise RuntimeError(
            "Rate limiting requires Redis in production. Set RATE_LIMIT_STORAGE_URI "
            "(or REDIS_URL). To accept process-local limits knowingly, set "
            "ALLOW_IN_MEMORY_RATE_LIMIT=true."
        )
    if is_production():
        logger.warning("Using process-local rate limits in production (explicitly allowed).")
    return "memory://"


def _trusted_proxy_hops() -> int:
    try:
        return max(0, int(os.getenv("TRUSTED_PROXY_HOPS", "0") or 0))
    except ValueError:
        return 0


def client_key(request: Request) -> str:
    """Identify the caller for rate limiting.

    On Render, use the Cloudflare-injected CF-Connecting-IP address. In other
    deployments, the socket address is used unless TRUSTED_PROXY_HOPS is set to
    the number of trusted proxies that append to X-Forwarded-For. The entry that
    many positions from the right is used; leftmost entries are client-controlled
    and spoofable. Invalid forwarded values are ignored.
    """
    if env_flag("RENDER"):
        # Render's Cloudflare edge overwrites this header with the visitor IP.
        # Validate it as an IP literal before using it as a quota key.
        cloudflare_ip = request.headers.get("cf-connecting-ip", "").strip()
        if cloudflare_ip:
            try:
                return ipaddress.ip_address(cloudflare_ip).compressed
            except ValueError:
                logger.warning("Ignoring invalid CF-Connecting-IP header")

    hops = _trusted_proxy_hops()
    if hops:
        entries = [
            part.strip()
            for header in request.headers.getlist("x-forwarded-for")
            for part in header.split(",")
            if part.strip()
        ]
        if len(entries) >= hops:
            return entries[-hops]
    return get_remote_address(request)


limiter = Limiter(
    key_func=client_key,
    storage_uri=resolve_storage_uri(),
    headers_enabled=True,
)
