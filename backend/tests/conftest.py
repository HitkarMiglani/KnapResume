import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://knapresume:knapresume@127.0.0.1:5432/knapresume_test"
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

engine = create_engine(settings.database_url)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _reset_schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_client(client):
    resp = client.post(
        "/api/auth/register", json={"email": "test@example.com", "password": "correct-horse"}
    )
    assert resp.status_code == 201
    csrf_token = resp.json()["csrf_token"]
    client.headers.update({"X-CSRF-Token": csrf_token})
    return client
