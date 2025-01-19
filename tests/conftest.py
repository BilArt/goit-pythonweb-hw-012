import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contacts_api.database import Base, get_db
from contacts_api.models import User
from contacts_api.utils import hash_password
from contacts_api.auth import get_current_user
from contacts_api.main import app

DATABASE_URL = "sqlite:///:memory:"

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

@pytest.fixture
def override_get_db(db_session):
    def _get_db_override():
        yield db_session
    app.dependency_overrides[get_db] = _get_db_override

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
def override_get_current_user(test_user):
    def mock_get_current_user():
        return test_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides[get_current_user] = None
