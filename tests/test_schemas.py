from contacts_api.schemas import ContactCreate, UserCreate
from pydantic import ValidationError
import pytest

def test_contact_create_valid_data():
    data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone": "123456789",
        "birthday": "1985-05-15",
        "additional_info": "Test user info"
    }
    contact = ContactCreate(**data)
    assert contact.first_name == "Jane"
    assert contact.email == "jane.doe@example.com"

def test_contact_create_invalid_email():
    data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "invalid-email",
        "phone": "123456789",
        "birthday": "1985-05-15",
        "additional_info": "Test user info"
    }
    with pytest.raises(ValidationError):
        ContactCreate(**data)

def test_user_create_valid_data():
    data = {
        "email": "user@example.com",
        "password": "securepassword",
        "full_name": "Example User"
    }
    user = UserCreate(**data)
    assert user.email == "user@example.com"
    assert user.full_name == "Example User"

def test_user_create_missing_password():
    data = {
        "email": "user@example.com",
        "full_name": "Example User"
    }
    with pytest.raises(ValidationError):
        UserCreate(**data)
