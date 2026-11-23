from sqlalchemy import inspect
from fastapi.testclient import TestClient

from app.main import app
from app import db
from app.models import MemoryEntry
from app.routers import plan as plan_router


def test_health():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_itinerary_plan_contract(monkeypatch):
    async def fake_generate_dynamic_itinerary(**kwargs):
        assert kwargs["destination"] == "Barcelona, Spain"
        assert kwargs["days"] == 2
        return {
            "summary": "A two-day Barcelona itinerary",
            "itinerary": [
                {"day": 1, "theme": "Architecture", "activities": [{"title": "Sagrada Familia"}]},
                {"day": 2, "theme": "Old Town", "activities": [{"title": "Gothic Quarter"}]},
            ],
            "highlights": ["Sagrada Familia", "Gothic Quarter", "Park Guell"],
            "estimated_budget": "Medium",
            "cultural_insights": "Catalan culture and local customs.",
            "local_recommendations": "Explore neighborhood markets.",
            "travel_tips": "Use public transport.",
            "ai_provider": "gemini",
        }

    monkeypatch.setattr(plan_router, "generate_dynamic_itinerary", fake_generate_dynamic_itinerary)
    client = TestClient(app)
    payload = {
        "from_city": "Kochi, India",
        "destination": "Barcelona, Spain",
        "departure_date": "2026-12-01",
        "return_date": "2026-12-02",
        "travelers": 2,
        "budget": "medium",
        "interests": ["culture", "food"],
    }

    response = client.post("/api/plan/", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["destination"] == payload["destination"]
    assert data["total_days"] == 2
    assert len(data["itinerary"]) == 2
    assert data["ai_provider"] == "gemini"


def test_signals():
    client = TestClient(app)
    response = client.get("/api/signals/?destination=Barcelona,%20Spain")
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_database_engine_uses_test_database(tmp_path, monkeypatch):
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setattr(db, "_engine", None)

    engine = db.get_engine()
    assert engine.url.database == str(database_path)

    db.create_db_and_tables()
    assert "memoryentry" in inspect(engine).get_table_names()
