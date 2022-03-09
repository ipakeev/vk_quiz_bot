from app import utils


def test_encode_password():
    password = "12345"
    encoded = utils.encode_password(password)
    assert isinstance(encoded, str)
    assert encoded != password
