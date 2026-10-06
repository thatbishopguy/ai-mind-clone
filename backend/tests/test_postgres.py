"""Run existing persistence workflows on a disposable PostgreSQL schema.

Set TEST_POSTGRES_URL to a test database; no existing tables are touched.
"""
import importlib
import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from app.core.config import Settings
from app.main import create_app

URL = os.environ.get("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="TEST_POSTGRES_URL is not configured")


@pytest.fixture
def postgres(monkeypatch):
    schema = "test_" + uuid4().hex
    connect = psycopg.connect
    with connect(URL) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))

    def isolated_connect(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        connection.commit()
        return connection

    monkeypatch.setattr(psycopg, "connect", isolated_connect)
    try:
        yield URL
    finally:
        with connect(URL) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.mark.parametrize("module,function", [
    ("test_decisions", "test_persists_across_application_sessions"),
    ("test_analysis", "test_structure_review_persist_and_preserve_m2"),
    ("test_ai", "test_preview_apply_review_history_and_stale"),
    ("test_ai", "test_no_key_fallback_leaves_saved_analysis_untouched"),
    ("test_scoring", "test_saved_evaluation_and_stale_context"),
])
def test_postgres_workflows(postgres, monkeypatch, tmp_path, module, function):
    tests = importlib.import_module(module)

    def hosted_settings(**kwargs):
        kwargs["database_url"] = postgres
        return Settings(**kwargs)

    monkeypatch.setattr(tests, "Settings", hosted_settings)
    getattr(tests, function)(tmp_path)


def test_postgres_create_list_fetch(postgres):
    from test_decisions import test_create_list_and_fetch
    with TestClient(create_app(Settings(database_url=postgres, _env_file=None))) as client:
        test_create_list_and_fetch(client)
