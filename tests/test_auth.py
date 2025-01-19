import pytest
from sqlalchemy.orm import Session
from contacts_api.auth import create_access_token
from contacts_api.models import User
from contacts_api.utils import hash_password, verify_password
from contacts_api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

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

def test_forgot_password(mocker, test_user, db_session):
    mock_send_email = mocker.patch("contacts_api.email_utils.send_email", return_value=None)

    payload = {"email": test_user.email}
    response = client.post("/auth/forgot-password", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset link sent to your email"
    mock_send_email.assert_called_once_with(
        "Сброс пароля",
        test_user.email,
        mocker.ANY
    )

def test_reset_password(mocker, test_user, db_session):
    reset_token = create_access_token({"sub": test_user.email})

    payload = {"token": reset_token, "new_password": "newsecurepassword"}
    response = client.post("/auth/reset-password", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Password has been reset successfully"

    updated_user = db_session.query(User).filter(User.email == test_user.email).first()
    assert updated_user is not None
    assert verify_password("newsecurepassword", updated_user.password)

def test_upload_avatar(mocker, test_user, auth_headers):
    mock_upload = mocker.patch("contacts_api.auth.upload", return_value={"public_id": "avatar_1"})
    mock_cloudinary_url = mocker.patch("contacts_api.auth.cloudinary_url", return_value=("http://example.com/avatar.jpg", None))

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
    mock_upload.assert_called_once()
    mock_cloudinary_url.assert_called_once()
