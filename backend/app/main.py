from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from .routers import itineraries, signals, memory, digest, chat, plan
from .services.llm_provider import get_ai_provider_info
from .startup import initialize_pipeline


def create_app() -> FastAPI:
    # Load .env if present for local development before provider configuration is read.
    load_dotenv()

    app = FastAPI(title="Nomad AI Backend", version="0.3.0")

    origins_raw = os.getenv("CORS_ORIGINS", "").strip()
    origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
    if not origins:
        origins = ["http://localhost:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(itineraries.router, prefix="/api/itineraries", tags=["itineraries"])
    app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
    app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
    app.include_router(digest.router, prefix="/api/digest", tags=["digest"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(plan.router, prefix="/api/plan", tags=["plan"])

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
            "platform": "NomadAI",
            "version": "0.3.0",
            "features": [
                "Google Gemini as the sole AI provider",
                "Server-side API key handling",
                "Configurable Gemini model via GEMINI_MODEL",
                "Multi-turn chat and itinerary generation",
            ],
        }

    @app.get("/api/pipeline-status")
    def pipeline_status():
        """Get pipeline status and component health."""
        from .startup import get_pipeline_status
        return get_pipeline_status()

    return app


app = create_app()
