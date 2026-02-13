import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from main import app
from database import Base, get_db
from sqlalchemy.pool import NullPool
from utils import hash_password
from models import User

SQLALCHEMY_DATABASE_URL = "postgresql://saeed:password@localhost:5432/vaultcore_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def db_setup():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield
    engine.dispose()
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_setup):
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.fixture()
def authenticated_user(client):
    with TestingSessionLocal() as db:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password123"),
            first_name="Test",
            last_name="User",
            gender="male",
            is_verified=True,
        )
        db.add(user)
        db.commit()
        user_id = user.id

    res = client.post(
        "/api/v1/auth/token", data={"username": "testuser", "password": "password123"}
    )
    token = res.json()["access_token"]
    return {"id": str(user_id), "header": {"Authorization": f"Bearer {token}"}}
