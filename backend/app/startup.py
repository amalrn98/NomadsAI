"""Readiness reporting for the itinerary pipeline."""


def get_pipeline_status():
    """Report pipeline readiness without running an itinerary generation.

    This is served by a public endpoint, so it must not call an LLM or any other
    cost-bearing service.
    """
    from .services.llm_provider import is_configured

    return {
        "status": "operational",
        "components": {
            "standalone_pipeline": "ready",
            "gemini": "configured" if is_configured() else "not_configured",
        },
        "note": "Static readiness check only; it does not exercise Gemini or the pipeline.",
    }
