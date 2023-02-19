from encryption import JWT, JWTException


def test_access_creation():
    expected = {'user_id': 33}
    access_token = JWT(expected, lifetime=600)
    encoded_access, expire_at = access_token.perform_encoding()
    decoded = JWT.decrypt(encoded_access)
    assert decoded == expected


def test_expired_token():
    expected = {'user_id': 33}
    access_token = JWT(expected, lifetime=-1)
    encoded_access, expire_at = access_token.perform_encoding()
    try:
        decoded = JWT.decrypt(encoded_access)
        assert False
    except JWTException:
        assert True
