from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

def test_login_user_not_found(test_credentials):
    with patch("controllers.auth_controller.get_user_by_email") as mock:
        mock.return_value = None
        response = client.post("/v1/auth/login", json=test_credentials)
        assert response.status_code == 401
        assert response.json()["message"] == "Invalid email or password"

def test_login_wrong_password(test_credentials):
    with patch("controllers.auth_controller.get_user_by_email") as mock, \
         patch("controllers.auth_controller.verify_password") as mock_verify:

        fake_user = MagicMock()
        fake_user.id = 1
        fake_user.email = test_credentials["email"]
        fake_user.hashed_password = "hashed_string"

        mock.return_value = fake_user
        mock_verify.return_value = False

        response = client.post("/v1/auth/login", json=test_credentials)

        assert response.status_code == 401
        assert response.json()["message"] == "Invalid email or password"
        mock_verify.assert_called_once_with(test_credentials["password"], "hashed_string")

def test_login_success(test_credentials):
    with patch("controllers.auth_controller.get_user_by_email") as mock, \
        patch("controllers.auth_controller.verify_password") as mock_verify, \
        patch("controllers.auth_controller.create_access_token") as mock_create_token, \
        patch("controllers.auth_controller.create_refresh_token") as mock_refresh, \
        patch("controllers.auth_controller.save_refresh_token") as mock_save:
        fake_user = MagicMock()
        fake_user.id = 1
        fake_user.email = test_credentials["email"]
        fake_user.hashed_password = "hashed_string"

        mock.return_value = fake_user
        mock_verify.return_value = True
        mock_create_token.return_value = "mocked_jwt_token_string"
        mock_refresh.return_value = ("mocked_refresh_token", MagicMock())
        mock_save.return_value = None

        response = client.post("/v1/auth/login", json=test_credentials)

        assert response.status_code == 200
        json_data = response.json()
        assert "access_token" in json_data
        assert json_data["access_token"] == "mocked_jwt_token_string"
        assert json_data["refresh_token"] == "mocked_refresh_token"
        assert json_data["token_type"] == "bearer"

        mock_verify.assert_called_once_with(test_credentials["password"], "hashed_string")
        mock_create_token.assert_called_once_with(data={"sub": "1", "role": fake_user.role})



def test_refresh_token_success():
    with patch("controllers.auth_controller.get_refresh_token") as mock_get, \
         patch("controllers.auth_controller.revoke_refresh_token") as mock_revoke, \
         patch("controllers.auth_controller.create_access_token") as mock_access, \
         patch("controllers.auth_controller.create_refresh_token") as mock_refresh, \
         patch("controllers.auth_controller.save_refresh_token") as mock_save:

        fake_token = MagicMock()
        fake_token.user_id = 1
        mock_get.return_value = fake_token
        mock_access.return_value = "new_access_token"
        mock_refresh.return_value = ("new_refresh_token", MagicMock())
        mock_save.return_value = None

        response = client.post("/v1/auth/refresh", json={"refresh_token": "old_valid_token"})

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["refresh_token"] == "new_refresh_token"
        assert data["token_type"] == "bearer"
        mock_revoke.assert_called_once()

def test_refresh_token_invalid():
    with patch("controllers.auth_controller.get_refresh_token") as mock_get:
        mock_get.return_value = None

        response = client.post("/v1/auth/refresh", json={"refresh_token": "expired_or_invalid_token"})

        assert response.status_code == 401
        assert response.json()["message"] == "Invalid or expired refresh token"

def test_logout_success():
    with patch("controllers.auth_controller.revoke_refresh_token") as mock_revoke:
        mock_revoke.return_value = None

        response = client.post("/v1/auth/logout", json={"refresh_token": "some_valid_token"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Logged out successfully"
