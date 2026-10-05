from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

DRAFT = {
    "situation": "Should I accept this cabinet installation project?",
    "domain": "Work",
    "stakes": "High",
    "time_pressure": "Moderate",
}


def settings_for(path: Path) -> Settings:
    return Settings(database_url=f"sqlite:///{path}", _env_file=None)


@pytest.fixture
def client(tmp_path: Path):
    with TestClient(create_app(settings_for(tmp_path / "nested" / "decisions.db"))) as client:
        yield client


def test_create_list_and_fetch(client: TestClient) -> None:
    assert client.get("/api/v1/decisions").json() == []
    response = client.post("/api/v1/decisions", json=DRAFT)
    assert response.status_code == 201
    saved = response.json()
    UUID(saved["id"])
    assert all(saved[key] == value for key, value in DRAFT.items())
    assert saved["created_at"] == saved["updated_at"]
    assert saved["created_at"].endswith("Z")
    second = client.post("/api/v1/decisions", json={**DRAFT, "situation": "Another decision to consider."}).json()
    assert second["id"] != saved["id"]
    listing = client.get("/api/v1/decisions")
    assert listing.headers["cache-control"] == "no-store"
    assert listing.json() == [second, saved]
    fetched = client.get(f"/api/v1/decisions/{saved['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == saved


@pytest.mark.parametrize("changes", [
    {"situation": "short"}, {"situation": " " * 20}, {"situation": None},
    {"domain": "unknown"}, {"stakes": "unknown"}, {"time_pressure": "unknown"},
    {"unexpected": True},
])
def test_invalid_requests_do_not_write(client: TestClient, changes: dict) -> None:
    assert client.post("/api/v1/decisions", json={**DRAFT, **changes}).status_code == 422
    assert client.get("/api/v1/decisions").json() == []


def test_missing_fields(client: TestClient) -> None:
    assert client.post("/api/v1/decisions", json={}).status_code == 422


def test_missing_decision(client: TestClient) -> None:
    response = client.get(f"/api/v1/decisions/{uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Decision not found"}
    assert client.get("/api/v1/decisions/not-a-uuid").status_code == 422


def test_trim_and_preserve_text(client: TestClient) -> None:
    text = "Should I say 'no'?\nOr reconsider? <script> is just text."
    response = client.post("/api/v1/decisions", json={**DRAFT, "situation": f"  {text}  "})
    assert response.status_code == 201
    saved = response.json()
    assert saved["situation"] == text
    assert client.get(f"/api/v1/decisions/{saved['id']}").json()["situation"] == text


def test_persists_across_application_sessions(tmp_path: Path) -> None:
    settings = settings_for(tmp_path / "persisted.db")
    with TestClient(create_app(settings)) as first:
        saved = first.post("/api/v1/decisions", json=DRAFT).json()
    with TestClient(create_app(settings)) as second:
        assert second.get("/api/v1/decisions").json() == [saved]
        assert second.get(f"/api/v1/decisions/{saved['id']}").json() == saved

