import pytest
from unittest.mock import MagicMock, patch
from dto.user_dto import UserCreateDTO
from services.user_service import register_user
from models.user import User

@patch("services.user_service.hash_password")
@patch("services.user_service.create_user")
@patch("services.user_service.get_user_by_email")
def test_register_user_success(mock_get_user,mock_create_user,mock_hash,)->None:
    mock_db=MagicMock()
    user_in=UserCreateDTO(email="newuser@example.com", password="Secure123!")

    mock_get_user.return_value=None
    mock_hash.return_value="hashed_mock_string"

    fake_user = User(id=1,email=user_in.email,hashed_password="hashed_mock_string")
    mock_create_user.return_value=fake_user

    result=register_user(db=mock_db,email=user_in.email,plain_password=user_in.password)

    assert result == fake_user
    assert result.email== "newuser@example.com"
    mock_get_user.assert_called_once_with(mock_db,user_email=user_in.email)
    mock_create_user.assert_called_once_with(db=mock_db, email="newuser@example.com", hashed_password="hashed_mock_string")

@patch("services.user_service.get_user_by_email")
def test_register_user_duplicate_email(mock_get_user)->None:
    mock_db = MagicMock()
    user_in = UserCreateDTO(email="existing@example.com", password="Secure123!")

    existing_user = User(id=1, email="existing@example.com", hashed_password="some_hash")
    mock_get_user.return_value = existing_user

    with pytest.raises(ValueError, match="Email already registered"):
        register_user(db=mock_db,email=user_in.email,plain_password=user_in.password)

    mock_get_user.assert_called_once_with(mock_db,user_email=user_in.email)
