import pytest
from jose import jwt
from fastapi import HTTPException, status
from config.settings import settings
from middlewares.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

def test_verify_password_correct():
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)

    assert verify_password(raw_password, hashed) is True

def test_verify_password_wrong():
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)

    assert verify_password("WrongPasswordString", hashed) is False

def test_create_access_token():
    payload_data = {"sub": "1"}
    token = create_access_token(data=payload_data)

    assert isinstance(token, str)

    decoded_payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm]
    )
    assert decoded_payload["sub"] == "1"
    assert "exp" in decoded_payload 

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    payload_data = {"sub":"42"}
    token = create_access_token(data=payload_data)

    user_payload =  await get_current_user(token=token)

    assert user_payload is not None
    assert user_payload["sub"] == "42"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    garbage_token = "invalid.token.payload.signature.here"

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=garbage_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
