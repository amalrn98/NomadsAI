# Itinerary pipeline

This directory contains itinerary generation and destination-knowledge pipeline code.

## Current role
The pipeline provides local destination knowledge, itinerary structure/enrichment, and retrieval logic used by backend features. Local data and generated SQLite/cache state are derived application data, not live travel inventory.

## Limitations
- Local destination knowledge is curated/static and may be incomplete or outdated.
- Static flight, hotel, and event fixtures elsewhere in backend/app/mock_data/ are demonstrations, not live pricing, schedules, inventory, or availability.
- Do not claim sub-second generation, production readiness, complete global coverage, or live verification without current measurements and tests.
- Generated local SQLite/cache files are ephemeral on hosted Render filesystems. They must be rebuildable and must never be durable user-owned storage.
- Gemini-backed behavior is handled through backend service modules and may require GEMINI_API_KEY.

## Code map
- standalone_pipeline.py: pipeline entry point (`generate_itinerary_pipeline`) with deterministic fallback.
- skeleton_builder.py: stage 1, itinerary structure generation.
- data_retriever.py: stage 2, enrichment from local destination knowledge.

Check current call sites and tests before changing pipeline behavior. The repository docs/ARCHITECTURE.md guide explains the subsystem's application role.

## Tests
Run the backend suite from backend/ with python -m pytest -q.
