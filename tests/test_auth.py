import pytest
from fastapi.testclient import TestClient
from contacts_api.auth import create_access_token
from contacts_api.models import User
from contacts_api.utils import verify_password
from contacts_api.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_forgot_password(mocker, test_user, db_session):
    async def mock_send_email(subject, recipient, body):
        return None

    mocker.patch("contacts_api.email_utils.send_email", mock_send_email)

    payload = {"email": test_user.email}
    response = client.post("/auth/forgot-password", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset link sent to your email"


@pytest.mark.asyncio
async def test_reset_password(mocker, test_user, db_session):
    async def mock_redis_get(key):
        return None

    async def mock_redis_delete(key):
        return None

    mocker.patch("contacts_api.auth.redis_client.get", mock_redis_get)
    mocker.patch("contacts_api.auth.redis_client.delete", mock_redis_delete)

    reset_token = create_access_token({"sub": test_user.email})

    payload = {"token": reset_token, "new_password": "newsecurepassword"}
    response = client.post("/auth/reset-password", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Password has been reset successfully"

    updated_user = db_session.query(User).filter(User.email == test_user.email).first()
    assert updated_user is not None
    assert verify_password("newsecurepassword", updated_user.password)


@pytest.mark.asyncio
async def test_upload_avatar(mocker, test_user, auth_headers):
    mock_upload = mocker.patch("contacts_api.auth.upload", new_callable=mocker.AsyncMock)
    mock_upload.return_value = {"public_id": "avatar_1"}

    mock_cloudinary_url = mocker.patch("contacts_api.auth.cloudinary_url", new_callable=mocker.AsyncMock)
    mock_cloudinary_url.return_value = ("http://example.com/avatar.jpg", None)

    with open("test_avatar.jpg", "wb") as f:
        f.write(b"fake_image_data")

    with open("test_avatar.jpg", "rb") as avatar_file:
        response = client.post(
            "/auth/upload-avatar",
            headers=auth_headers,
            files={"file": ("avatar.jpg", avatar_file, "image/jpeg")},
        )

    assert response.status_code == 200
    assert response.json()["avatar_url"] == "http://example.com/avatar.jpg"
    mock_upload.assert_awaited_once()
    mock_cloudinary_url.assert_awaited_once()
