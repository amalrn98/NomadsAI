"""Shared rate limiter for public, cost-bearing API endpoints."""

import os

from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address

load_dotenv()

# Use Redis when configured so limits are shared across backend instances.
# The in-memory store is a development/single-instance fallback only.
storage_uri = os.getenv("RATE_LIMIT_STORAGE_URI") or os.getenv("REDIS_URL") or "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    headers_enabled=True,
)
