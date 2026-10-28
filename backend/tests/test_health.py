from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.api.v1.endpoints import health


@pytest.mark.parametrize("revisions", [(), ("20261006_0002",)])
def test_health_rejects_missing_or_outdated_migrations(monkeypatch, revisions):
    connection = MagicMock()
    connection.dialect.name = "postgresql"
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(health.database, "engine", engine)
    migration_context = MagicMock()
    migration_context.get_current_heads.return_value = revisions
    monkeypatch.setattr(health.MigrationContext, "configure", lambda conn: migration_context)

    with pytest.raises(HTTPException) as error:
        health.health()

    assert error.value.status_code == 503
    assert "alembic upgrade head" in error.value.detail


def test_health_accepts_current_postgres_schema(monkeypatch):
    connection = MagicMock()
    connection.dialect.name = "postgresql"
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(health.database, "engine", engine)
    migration_context = MagicMock()
    migration_context.get_current_heads.return_value = tuple(health._required_revisions)
    monkeypatch.setattr(health.MigrationContext, "configure", lambda conn: migration_context)

    assert health.health()["database"] == "ok"


def test_health_reports_unreachable_database(monkeypatch):
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("SELECT 1", {}, Exception("unavailable"))
    monkeypatch.setattr(health.database, "engine", engine)

    with pytest.raises(HTTPException) as error:
        health.health()

    assert error.value.status_code == 503
    assert error.value.detail == "Database unavailable"
