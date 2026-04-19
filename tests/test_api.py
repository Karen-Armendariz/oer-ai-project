import pytest
from fastapi.testclient import TestClient

from backend.api import app, get_service


class _FakeOERService:
    def search(self, course_query=None, syllabus_text=None):
        return {
            "query": course_query,
            "syllabus_source": None,
            "keywords": ["demo"],
            "results": [
                {
                    "title": "Sample OER",
                    "license": "CC BY",
                    "creators": "Author",
                    "links": "[]",
                    "distance": 0.5,
                    "keyword_overlap": 2,
                    "score": 75.0,
                }
            ],
            "ingest_error": None,
        }


@pytest.fixture
def client():
    app.dependency_overrides[get_service] = lambda: _FakeOERService()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "chroma_ready" in body


def test_search_ok(client):
    response = client.post("/oer/search", json={"course_query": "BIOL 1101K"})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "BIOL 1101K"
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Sample OER"


def test_search_empty_body(client):
    response = client.post("/oer/search", json={})
    assert response.status_code in (400, 422)


def test_search_short_course_query(client):
    response = client.post("/oer/search", json={"course_query": "AB"})
    assert response.status_code in (400, 422)
