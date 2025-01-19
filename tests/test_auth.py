ACCESS_TOKEN_EXPIRE_MINUTES = 30

import pytest
from contacts_api.auth import create_access_token, get_current_user
from jose import jwt
from contacts_api.models import User
from unittest.mock import AsyncMock
import json
from contacts_api.utils import hash_password

SECRET_KEY = "q84vNKq3mZTuE9PJd6cYLBHZK7A2RPXt"
ALGORITHM = "HS256"

@pytest.fixture
def test_user(db_session):
    email = "testuser@example.com"
    password = "securepassword"
    hashed_password = hash_password(password)

    db_session.query(User).filter(User.email == email).delete()
    db_session.commit()

    user = User(email=email, password=hashed_password, full_name="Test User", is_verified=True)
    db_session.add(user)
    db_session.commit()

    return user

@pytest.fixture
def mock_redis(mocker):
    mocker.patch("contacts_api.auth.redis_client.get", new_callable=AsyncMock)
    mocker.patch("contacts_api.auth.redis_client.setex", new_callable=AsyncMock)

def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user_from_redis(mocker):
    cached_data = json.dumps({
        "id": 1,
        "email": "testuser@example.com",
        "full_name": "Test User",
        "is_verified": True,
    })
    mocker.patch("contacts_api.auth.redis_client.get", new_callable=AsyncMock, return_value=cached_data)

    token = jwt.encode({"sub": "testuser@example.com"}, SECRET_KEY, algorithm=ALGORITHM)

    user = await get_current_user(token=token, db=None)

    assert user.email == "testuser@example.com"
    assert user.full_name == "Test User"

@pytest.mark.asyncio
async def test_set_current_user_to_redis(mocker, db_session, test_user):
    mocker.patch("contacts_api.auth.redis_client.get", new_callable=AsyncMock, return_value=None)
    mock_setex = mocker.patch("contacts_api.auth.redis_client.setex", new_callable=AsyncMock)

    token = jwt.encode({"sub": test_user.email}, SECRET_KEY, algorithm=ALGORITHM)

    user = db_session.query(User).filter(User.email == test_user.email).first()
    assert user is not None

    await get_current_user(token=token, db=db_session)

    mock_setex.assert_called_once_with(
        test_user.email,
        ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        json.dumps({
            "id": test_user.id,
            "email": test_user.email,
            "full_name": test_user.full_name,
            "is_verified": test_user.is_verified,
        }),
    )
