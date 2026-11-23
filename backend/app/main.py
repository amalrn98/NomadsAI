from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

from .rate_limit import limiter
from .routers import itineraries, signals, digest, chat, plan, memory
from .services.llm_provider import get_ai_provider_info


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
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(itineraries.router, prefix="/api/itineraries", tags=["itineraries"])
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

    @app.get("/api/pipeline-status")
    def pipeline_status():
        """Get pipeline status and component health."""
        from .startup import get_pipeline_status
        return get_pipeline_status()

    return app


app = create_app()
