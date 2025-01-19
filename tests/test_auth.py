import pytest
from fastapi.testclient import TestClient
from contacts_api.auth import create_access_token
from contacts_api.main import app
import tempfile

client = TestClient(app)

@pytest.mark.asyncio
async def test_forgot_password(mocker, test_user, db_session):
    mock_send_email = mocker.patch("contacts_api.auth.send_email", new_callable=mocker.AsyncMock)
    mock_send_email.return_value = None

    client_spy = mocker.spy(client, "post")

    payload = {"email": test_user.email}
    response = client.post("/auth/forgot-password", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset link sent to your email"
    mock_send_email.assert_awaited_once_with(
        "Сброс пароля", test_user.email, mocker.ANY
    )

    assert client_spy.call_count == 1


@pytest.mark.asyncio
async def test_reset_password(mocker, test_user, db_session, mock_redis):
    mock_redis.get.return_value = None
    mock_redis.delete.return_value = 1

    reset_token = create_access_token({"sub": test_user.email})

    payload = {"token": reset_token, "new_password": "newsecurepassword"}
    response = client.post("/auth/reset-password", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Password has been reset successfully"

    mock_redis.get.assert_awaited_once_with(test_user.email)
    mock_redis.delete.assert_awaited_once_with(test_user.email)

@pytest.mark.asyncio
async def test_upload_avatar(mocker, test_user, auth_headers):
    mock_upload = mocker.patch("contacts_api.auth.upload", new_callable=mocker.AsyncMock)
    mock_upload.return_value = {"public_id": "avatar_1"}

    mock_cloudinary_url = mocker.patch(
        "contacts_api.auth.cloudinary_url",
        return_value=("http://example.com/avatar.jpg", None),
    )

    with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
        temp_file.write(b"fake_image_data")
        temp_file.seek(0)
        response = client.post(
            "/auth/upload-avatar",
            headers=auth_headers,
            files={"file": ("avatar.jpg", temp_file, "image/jpeg")},
        )

    assert response.status_code == 200
    assert response.json()["avatar_url"] == "http://example.com/avatar.jpg"

    mock_upload.assert_awaited_once()
    mock_cloudinary_url.assert_called_once_with("avatar_1", format="jpg")
