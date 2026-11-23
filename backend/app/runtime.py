"""Small helpers for detecting the deployment environment."""

import os

_TRUTHY = {"1", "true", "yes", "on"}


def env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUTHY


def is_production() -> bool:
    """True on Render (which sets RENDER=true) or when APP_ENV/ENVIRONMENT is production."""
    if env_flag("RENDER"):
        return True
    for name in ("APP_ENV", "ENVIRONMENT"):
        if os.getenv(name, "").strip().lower() == "production":
            return True
    return False
