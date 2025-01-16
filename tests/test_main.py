from fastapi.testclient import TestClient
from contacts_api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 404  

def test_protected_route_without_auth():
    response = client.get("/contacts/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_register_user(mocker):
    mock_send_email = mocker.patch("contacts_api.email_utils.send_email", return_value=None)
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

def test_login_user(mocker):
    mock_verify_password = mocker.patch("contacts_api.utils.verify_password", return_value=True)
    mocker.patch("contacts_api.auth.get_db", return_value=iter([]))  # Mock базы данных
    response = client.post(
        "/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "securepassword"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    mock_verify_password.assert_called_once()
