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

@pytest.fixture(scope="function", autouse=True)
def setup_database(test_engine):
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="module")
def setup_db(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

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
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Contacts API!"}

def test_protected_route_without_auth():
    response = client.get("/contacts/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_register_user(mocker, db_session):
    mocker.patch("contacts_api.email_utils.send_email", return_value=None)

    user_data = {
        "email": "newuser@example.com",
        "password": "securepassword",
        "full_name": "New User"
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    db_user = db_session.query(User).filter_by(email=user_data["email"]).first()
    assert db_user is not None
    assert db_user.email == user_data["email"]
    assert db_user.full_name == user_data["full_name"]


@pytest.mark.asyncio
async def test_login_user(mocker, test_user):
    mocker.patch("contacts_api.utils.verify_password", return_value=True)
    mocker.patch("contacts_api.auth.get_db", return_value=iter([test_user]))

    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "securepassword",
            "full_name": test_user.full_name,
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
