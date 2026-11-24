import logging
import secrets

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

from .rate_limit import limiter
from .routers import signals, digest, chat, plan, memory
from .services.llm_provider import get_ai_provider_info, generate_completion, stream_completion

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    load_dotenv()

    app = FastAPI(title="NomadsAI Backend", version="0.4.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    origins_raw = os.getenv("CORS_ORIGINS", "").strip()
    origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
    if not origins:
        origins = ["http://localhost:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
    app.include_router(digest.router, prefix="/api/digest", tags=["digest"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(plan.router, prefix="/api/plan", tags=["plan"])
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])

    @app.get("/")
    def root():
        return {"service": "NomadsAI backend", "status": "ok", "docs": "/docs", "health": "/healthz"}

    @app.get("/healthz")
    def healthcheck():
        return {"status": "ok"}

    @app.get("/readyz")
    def readiness():
        """Report required production configuration separately from process liveness."""
        checks = {
            "gemini": bool(os.getenv("GEMINI_API_KEY", "").strip()),
            "supabase": bool(
                os.getenv("SUPABASE_URL", "").strip()
                and os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
            ),
            "redis": bool(
                (os.getenv("RATE_LIMIT_STORAGE_URI") or os.getenv("REDIS_URL") or "").strip()
            ),
        }
        if not all(checks.values()):
            raise HTTPException(
                status_code=503,
                detail={"status": "not_ready", "checks": checks},
            )
        return {"status": "ready", "checks": checks}

    @app.post("/internal/smoke/gemini", include_in_schema=False)
    async def gemini_smoke(request: Request, response: Response):
        """Run a protected, synthetic generation and streaming check on manual request."""
        expected_token = os.getenv("SMOKE_TEST_TOKEN", "").strip()
        supplied_token = request.headers.get("x-smoke-test-token", "")
        if not expected_token or not secrets.compare_digest(supplied_token, expected_token):
            raise HTTPException(status_code=404, detail="Not found.")

        messages = [{
            "role": "user",
            "content": "Reply with exactly this token and no other text: NOMADSAI_SMOKE_OK",
        }]
        try:
            generated = await generate_completion(
                messages, temperature=0, max_output_tokens=16
            )
            if "NOMADSAI_SMOKE_OK" not in generated:
                raise RuntimeError("Synthetic generation did not return the expected token.")

            streamed = "".join([
                chunk async for chunk in stream_completion(
                    messages, temperature=0, max_output_tokens=16
                )
            ])
            if "NOMADSAI_SMOKE_OK" not in streamed:
                raise RuntimeError("Synthetic streaming did not return the expected token.")
        except Exception as exc:
            logger.error("Protected production Gemini smoke test failed (%s)", type(exc).__name__)
            raise HTTPException(
                status_code=503,
                detail="The synthetic AI smoke test failed.",
            ) from exc

        return {"status": "ok", "generation": "ok", "streaming": "ok"}

    @app.get("/api/ai-status")
    def ai_status():
        """Return configured Gemini provider status without exposing credentials."""
        configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
        return {
            "status": "active" if configured else "configuration_required",
            "ai_providers": get_ai_provider_info(),
            "platform": "NomadsAI",
            "version": "0.4.0",
            "features": [
                "Google Gemini as the sole AI provider",
                "Server-side API key handling",
                "Configurable Gemini model via GEMINI_MODEL",
                "Multi-turn chat and itinerary generation",
                "Supabase Auth protected travel memories",
            ],
        }

    return app


app = create_app()
