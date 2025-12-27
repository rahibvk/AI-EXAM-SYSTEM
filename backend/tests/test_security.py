from app.core.security import verify_password, get_password_hash

def test_password_hashing():
    password = "secret_password"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)

def test_password_verification_fail():
    password = "secret_password"
    hashed = get_password_hash(password)
    assert not verify_password("wrong_password", hashed)
