from contacts_api.utils import hash_password, verify_password

def test_hash_password():
    password = "securepassword"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)

def test_verify_password():
    assert verify_password("securepassword", hash_password("securepassword"))
    assert not verify_password("wrongpassword", hash_password("securepassword"))
