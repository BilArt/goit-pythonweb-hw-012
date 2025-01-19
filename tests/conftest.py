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
from unittest.mock import AsyncMock

DATABASE_URL = "sqlite:///:memory:"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(autouse=True)
def override_get_db(db_session):
    def _get_db_override():
        yield db_session
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides[get_db] = None

@pytest.fixture
def test_user(db_session: Session):
    email = "testuser@example.com"
    password = "securepassword"
    hashed_password = hash_password(password)
    user = User(email=email, password=hashed_password, full_name="Test User", is_verified=True)
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def override_get_current_user(test_user):
    def mock_get_current_user(token: str = Depends(oauth2_scheme)) -> User:
        return test_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides[get_current_user] = None

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock_redis_client = mocker.MagicMock(spec=redis.Redis)
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.delete = AsyncMock(return_value=1)
    mocker.patch("contacts_api.auth.redis_client", mock_redis_client)
    return mock_redis_client