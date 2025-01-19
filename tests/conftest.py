from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contacts_api.database import Base, get_db
from contacts_api.models import User
from contacts_api.utils import hash_password
from contacts_api.auth import create_access_token, get_current_user
from contacts_api.main import app
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///:memory:"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    logger.info("Test engine created and database schema initialized.")
    yield engine
    Base.metadata.drop_all(bind=engine)
    logger.info("Test engine disposed and database schema dropped.")

@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    logger.info("Database session started.")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        logger.info("Database session closed.")

@pytest.fixture(autouse=True)
def override_get_db(db_session):
    def _get_db_override():
        yield db_session
    app.dependency_overrides[get_db] = _get_db_override
    logger.info("Dependency 'get_db' overridden with test session.")
    yield
    app.dependency_overrides[get_db] = None
    logger.info("Dependency 'get_db' override removed.")

@pytest.fixture
def test_user(db_session: Session):
    email = "testuser@example.com"
    password = "securepassword"
    hashed_password = hash_password(password)
    user = User(email=email, password=hashed_password, full_name="Test User", is_verified=True)
    db_session.add(user)
    db_session.commit()
    logger.info("Test user created: %s", email)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"sub": test_user.email})
    logger.info("Authorization headers created for test user: %s", test_user.email)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def override_get_current_user(test_user):
    def mock_get_current_user(token: str = Depends(oauth2_scheme)) -> User:
        return test_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    logger.info("Dependency 'get_current_user' overridden for test user.")
    yield
    app.dependency_overrides[get_current_user] = None
    logger.info("Dependency 'get_current_user' override removed.")

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock_redis_client = mocker.AsyncMock()
    mock_redis_client.get = mocker.AsyncMock(return_value=json.dumps({"id": 1, "email": "testuser@example.com"}))
    mock_redis_client.setex = mocker.AsyncMock(return_value=True)
    mock_redis_client.delete = mocker.AsyncMock(return_value=1)

    mocker.patch("contacts_api.auth.redis_client", mock_redis_client)

    return mock_redis_client
