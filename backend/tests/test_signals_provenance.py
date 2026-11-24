from fastapi.testclient import TestClient

from app.main import app
from app.routers import signals as signals_router


def test_static_signal_fixtures_are_explicitly_marked_as_samples(monkeypatch):
    fixtures = {
        "events.json": [{
            "name": "Example Festival",
            "location": "Example City",
            "start_date": "2099-05-01",
            "region": "Europe",
        }],
        "flights.json": [{
            "from": "AAA",
            "to": "Example City",
            "price": 100,
            "found_at": "2099-01-01T10:00:00Z",
            "region": "Europe",
        }],
        "hotels.json": [{
            "name": "Example Hotel",
            "city": "Example City",
            "price_per_night": 50,
            "date": "2099-01-01",
            "region": "Europe",
        }],
    }
    monkeypatch.setattr(
        signals_router,
        "_load_json",
        lambda filename: fixtures[filename],
    )

    response = TestClient(app).get("/api/signals/?destination=Example%20City")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(item["data_status"] == "sample" for item in data)
    assert all(item["is_live"] is False for item in data)
    assert all(item["verified"] is False for item in data)
    assert all(item["source"] == "local_fixture" for item in data)
    assert all("Demonstration data only" in item["data_notice"] for item in data)


def test_online_news_includes_source_and_retrieval_provenance(monkeypatch):
    fixtures = {
        "events.json": [],
        "flights.json": [],
        "hotels.json": [],
    }
    monkeypatch.setattr(
        signals_router,
        "_load_json",
        lambda filename: fixtures[filename],
    )
    monkeypatch.setattr(
        signals_router,
        "search_news",
        lambda query, max_results: [{
            "title": "Example travel event",
            "href": "https://example.com/event",
            "source": "Example News",
            "snippet": "An event announcement.",
            "date": "2099-05-01",
        }],
    )

    response = TestClient(app).get(
        "/api/signals/?destination=Example%20City&online_mode=true"
    )
    assert response.status_code == 200
    item = response.json()[0]
    assert item["data_status"] == "live_search_result"
    assert item["is_live"] is True
    assert item["verified"] is False
    assert item["source_url"] == "https://example.com/event"
    assert item["source_name"] == "Example News"
    assert item["retrieved_at"]
    assert "verify details" in item["data_notice"].lower()



def test_online_news_search_failure_keeps_sample_results_available(monkeypatch):
    fixtures = {
        "events.json": [{
            "name": "Example Festival",
            "location": "Example City",
            "start_date": "2099-05-01",
            "region": "Europe",
        }],
        "flights.json": [],
        "hotels.json": [],
    }
    monkeypatch.setattr(
        signals_router,
        "_load_json",
        lambda filename: fixtures[filename],
    )

    def fail_search(query, max_results):
        raise RuntimeError("search provider unavailable")

    monkeypatch.setattr(signals_router, "search_news", fail_search)

    response = TestClient(app).get(
        "/api/signals/?destination=Example%20City&online_mode=true"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["data_status"] == "sample"
    assert data[0]["verified"] is False
    assert data[0]["is_live"] is False
