import pytest
from validators import (
    validate_password,
    validate_event_type,
    validate_source,
    validate_payload
)

def test_validate_password_success():
    valid_pass="Secure123!"
    assert validate_password(valid_pass)==valid_pass
def test_validate_password_too_short():
    with pytest.raises(ValueError,match="at least 6 characters"):
        validate_password("Sec1")
def test_validate_password_no_uppercase():
    with pytest.raises(ValueError,match="at least one uppercase letter"):
        validate_password("secure123!")
def test_validate_password_no_digit():
    with pytest.raises(ValueError,match="at least one digit"):
        validate_password("Secure!")
def test_validate_password_no_special_char():
    with pytest.raises(ValueError,match="at least one special character"):
        validate_password("Secure123")



def test_validate_event_type_success():
    assert validate_event_type("user_login")=="USER_LOGIN"
    assert validate_event_type("PURCHASE")=="PURCHASE"
def test_validate_event_type_invalid():
    with pytest.raises(ValueError,match="event_type must be one of"):
        validate_event_type("INVALID_EVENT")


def test_validate_source_success():
    assert validate_source(" web-client ") == "web-client"
def test_validate_source_blank():
    with pytest.raises(ValueError,match="source must not be blank"):
        validate_source("  ")
    with pytest.raises(ValueError,match="source must not be blank"):
        validate_source("")


def test_validate_payload_success():
    valid_payload={"item_id":42,"quantity":1}
    assert validate_payload(valid_payload)==valid_payload
def test_validate_payload_empty():
    with pytest.raises(ValueError,match="payload must not be empty"):
        validate_payload({})