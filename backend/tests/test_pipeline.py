"""Deterministic tests for the two-stage itinerary pipeline and fallback."""

from app.pipeline import (
    build_skeleton,
    validate_skeleton,
    enrich_skeleton,
    generate_itinerary_pipeline,
)


def test_skeleton_builder_uses_valid_fallback_when_gemini_is_unconfigured(monkeypatch):
    monkeypatch.setattr("app.pipeline.skeleton_builder.is_configured", lambda: False)

    skeleton = build_skeleton(
        "London", 3, "New York", "luxury", ["culture", "food"]
    )

    assert skeleton["destination"] == "London"
    assert skeleton["total_days"] == 3
    assert len(skeleton["itinerary"]) == 3
    assert validate_skeleton(skeleton)


def test_data_retriever_enriches_skeleton_without_external_services(monkeypatch):
    monkeypatch.setattr("app.pipeline.skeleton_builder.is_configured", lambda: False)
    skeleton = build_skeleton(
        "London", 2, "New York", "medium", ["culture", "food"]
    )

    enriched = enrich_skeleton(skeleton)

    assert enriched["destination"] == "London"
    assert len(enriched["itinerary"]) == 2
    assert enriched["enrichment_info"]["enrichment_success"] is True


def test_full_pipeline_returns_structured_fallback():
    itinerary = generate_itinerary_pipeline(
        "Paris", 2, "London", "medium", ["art", "food"]
    )

    assert itinerary["destination"] == "Paris"
    assert itinerary["total_days"] == 2
    assert len(itinerary["itinerary"]) == 2
    assert itinerary["pipeline_info"]["pipeline_type"] == "fallback_template"
