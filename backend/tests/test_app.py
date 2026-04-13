from fastapi.testclient import TestClient

import app
import requests


client = TestClient(app.app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}


def test_ranked_inventors_endpoint_returns_sorted_results(monkeypatch):
    def fake_ranked_inventors():
        return [
            {
                "inventor_id": 1,
                "first_name": "Ada",
                "last_name": "Lovelace",
                "patent_count": 1,
                "technology_domains": ["Health"],
            },
            {
                "inventor_id": 2,
                "first_name": "Grace",
                "last_name": "Hopper",
                "patent_count": 3,
                "technology_domains": ["AI/ML"],
            },
        ]

    monkeypatch.setattr(app, "get_ranked_inventors_data", fake_ranked_inventors)

    response = client.get("/ranked-inventors")

    assert response.status_code == 200
    payload = response.json()
    assert [item["inventor_id"] for item in payload] == [2, 1]
    assert payload[0]["inventor_name"] == "Grace Hopper"
    assert payload[0]["fit_score"] == 10.0


def test_search_endpoint_without_auto_sync_uses_local_results(monkeypatch):
    def fake_search_local_patents(keyword):
        assert keyword == "ai"
        return [{"patent_id": 101, "title": "AI system"}]

    monkeypatch.setattr(app, "search_local_patents", fake_search_local_patents)

    response = client.get("/search", params={"keyword": "ai", "auto_sync": "false"})

    assert response.status_code == 200
    assert response.json() == [{"patent_id": 101, "title": "AI system"}]


def test_search_endpoint_with_auto_sync_returns_full_sync_payload(monkeypatch):
    def fake_sync_patents_for_keyword(keyword):
        assert keyword == "ai"
        return {
            "keyword": keyword,
            "message": "Sync completed.",
            "live_import_enabled": True,
            "has_live_matches": True,
            "local_match_count": 1,
            "local_matches": [{"patent_id": 101, "title": "AI system"}],
            "fetched_count": 2,
            "inserted_count": 1,
            "skipped_count": 1,
            "inventor_names_processed": 0,
            "inventor_links_created": 0,
            "errors": [],
        }

    monkeypatch.setattr(app, "sync_patents_for_keyword", fake_sync_patents_for_keyword)

    response = client.get("/search", params={"keyword": "ai", "auto_sync": "true"})

    assert response.status_code == 200
    assert response.json()["local_matches"] == [{"patent_id": 101, "title": "AI system"}]
    assert response.json()["fetched_count"] == 2


def test_inventors_endpoint_returns_service_error_details(monkeypatch):
    def fake_list_inventors():
        raise requests.RequestException("network down")

    monkeypatch.setattr(app, "list_inventors", fake_list_inventors)

    response = client.get("/inventors")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Inventor data service is unavailable. Check Supabase connectivity and credentials."
    }
