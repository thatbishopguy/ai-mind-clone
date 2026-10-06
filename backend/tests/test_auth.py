from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_production_requires_access_credentials():
    with pytest.raises(ValueError, match="Production requires"):
        create_app(Settings(app_env="production", _env_file=None))


def test_private_api_and_public_health(tmp_path: Path):
    settings = Settings(app_env="production", database_url=f"sqlite:///{tmp_path / 'private.db'}",
                        owner_username="owner", owner_password="test-only-password", _env_file=None)
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/health").status_code == 200
        for path in ("/", "/api/v1/decisions"):
            assert client.get(path).status_code == 401
            assert client.get(path, auth=("owner", "wrong")).status_code == 401
            assert client.get(path, auth=("wrong", "test-only-password")).status_code == 401
            assert client.get(path, auth=("owner", "test-only-password")).status_code == 200
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.post("/api/v1/decisions", json={}).status_code == 401


def test_partial_credentials_rejected():
    with pytest.raises(ValueError, match="Set both"):
        create_app(Settings(owner_password="test-only-password", _env_file=None))
