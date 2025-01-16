from contacts_api.models import User, Contact

def test_user_model():
    user = User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        password="hashedpassword",
        is_verified=False
    )
    assert user.email == "test@example.com"
    assert not user.is_verified

def test_contact_model():
    contact = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="123456789",
        birthday="1990-01-01",
        additional_info="Friend",
        user_id=1
    )
    assert contact.first_name == "John"
    assert contact.email == "john.doe@example.com"
