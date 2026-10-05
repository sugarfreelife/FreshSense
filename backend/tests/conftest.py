import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from dotenv import dotenv_values

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = (
    os.getenv("TEST_DATABASE_URL")
    or dotenv_values(BACKEND_DIR / ".env").get("TEST_DATABASE_URL")
    or ""
).strip()
if TEST_DATABASE_URL.startswith("postgres://"):
    TEST_DATABASE_URL = "postgresql+psycopg2://" + TEST_DATABASE_URL[len("postgres://") :]
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "Set TEST_DATABASE_URL to a dedicated PostgreSQL test database whose name ends with '_test'."
    )
test_database = make_url(TEST_DATABASE_URL)
if not test_database.drivername.startswith("postgresql") or not (test_database.database or "").endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL must point to a PostgreSQL database whose name ends with '_test'.")

# Ensure settings and the application's initial engine also target the test DB,
# even when backend/.env points at the developer's application database.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("JWT_SECRET", "test-only-secret-for-freshsense-at-least-32-bytes")

import app.core.database as database
from app.core.deps import get_db
from app.main import app
from app.models import Base

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10},
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def isolated_postgres_database(monkeypatch):
    """Reset the dedicated test database and route app database access to it."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", TestingSession)


@pytest.fixture()
def client(isolated_postgres_database):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    email = "tester@example.com"
    password = "secret123"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
