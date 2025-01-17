import pytest
from contacts_api.auth import create_access_token, get_current_user
from jose import jwt
from datetime import timedelta
from contacts_api.models import User

SECRET_KEY = "q84vNKq3mZTuE9PJd6cYLBHZK7A2RPXt"
ALGORITHM = "HS256"

@pytest.fixture
def test_user():
    return User(id=1, email="test@example.com", full_name="Test User", is_verified=True)

@pytest.fixture
def mock_redis(mocker):
    mocker.patch("contacts_api.auth.redis_client.get", return_value=None)
    mocker.patch("contacts_api.auth.redis_client.setex", return_value=None)


def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user(test_user, mocker):
    mocker.patch("contacts_api.auth.jwt.decode", return_value={"sub": test_user.email})
    mocker.patch("contacts_api.auth.get_db", return_value=[test_user])
    user = await get_current_user(token="dummy", db=None)  # Добавить await
    assert user.email == test_user.email

@pytest.mark.asyncio
async def test_get_current_user(test_user, mocker):
    mocker.patch("contacts_api.auth.redis_client.get", return_value=None)
    mocker.patch("contacts_api.auth.redis_client.setex", return_value=None)
    
    mocker.patch("contacts_api.auth.jwt.decode", return_value={"sub": test_user.email})
    mocker.patch("contacts_api.auth.get_db", return_value=[test_user])

    user = await get_current_user(token="dummy", db=None)
    assert user.email == test_user.email
