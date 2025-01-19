from fastapi.testclient import TestClient
import pytest
from contacts_api.main import app
from contacts_api.auth import create_access_token
from contacts_api.models import Contact, User
from contacts_api.utils import hash_password
from sqlalchemy.orm import Session

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
    assert token
    return {"Authorization": f"Bearer {token}"}

def test_create_contact(db_session, auth_headers):
    contact_data = {"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com"}
    response = client.post("/contacts/", json=contact_data, headers=auth_headers)
    assert response.status_code == 200

    db_contact = db_session.query(Contact).filter(Contact.email == contact_data["email"]).first()
    assert db_contact is not None
    assert db_contact.first_name == "John"

def test_get_contacts(db_session, auth_headers):
    contact = Contact(first_name="John", last_name="Doe", email="john.doe@example.com", user_id=1)
    db_session.add(contact)
    db_session.commit()

    response = client.get("/contacts/", headers=auth_headers)
    assert response.status_code == 200
    contacts = response.json()
    assert len(contacts) > 0

def test_delete_contact(db_session, auth_headers):
    contact = Contact(first_name="John", last_name="Doe", email="john.doe@example.com", user_id=1)
    db_session.add(contact)
    db_session.commit()

    response = client.delete(f"/contacts/{contact.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Contact deleted successfully"

    db_contact = db_session.query(Contact).filter(Contact.id == contact.id).first()
    assert db_contact is None
