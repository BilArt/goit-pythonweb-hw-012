from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contacts_api.main import app
from contacts_api.models import User
from contacts_api.utils import hash_password
from contacts_api.database import Base, get_db

DATABASE_URL = "sqlite:///:memory:"
client = TestClient(app)

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

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

    db_session.query(User).filter_by(email=email).delete()
    db_session.commit()
    db_session.add(user)
    db_session.commit()
    return user

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 404

def test_protected_route_without_auth():
    response = client.get("/contacts/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_register_user(mocker, db_session):
    mock_send_email = mocker.patch("contacts_api.email_utils.send_email", return_value=None)

    db_session.query(User).filter_by(email="testuser@example.com").delete()
    db_session.commit()

    response = client.post(
        "/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "securepassword",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "testuser@example.com"
    mock_send_email.assert_called_once()

def test_login_user(mocker, test_user):
    mock_verify_password = mocker.patch("contacts_api.utils.verify_password", return_value=True)

    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "securepassword"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    mock_verify_password.assert_called_once()
