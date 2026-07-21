from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock 
from main import app

client = TestClient(app)

def test_login_user_not_found():
    with patch("controllers.auth_controller.get_user_by_email") as mock:
        mock.return_value = None
        response = client.post("/auth/login",json={"email": "x@x.com","password":"Test123!"})
        assert response.status_code == 401
        assert response.json()["message"]=="Invalid email or password"

def test_login_wrong_password():
    with patch("controllers.auth_controller.get_user_by_email") as mock,\
         patch("controllers.auth_controller.verify_password") as mock_verify:
        
        fake_user = MagicMock()
        fake_user.id=1
        fake_user.email = "user@example.com"
        fake_user.hashed_password = "hashed_string"

        mock.return_value = fake_user
        mock_verify.return_value = False
        
        response = client.post("/auth/login", json={"email":"user@example.com","password":"Wrong@Password!"})

        assert response.status_code == 401
        assert response.json()["message"] == "Invalid email or password"
        mock_verify.assert_called_once_with("Wrong@Password!","hashed_string")

def test_login_success():
    with patch("controllers.auth_controller.get_user_by_email") as mock,\
         patch("controllers.auth_controller.verify_password") as mock_verify, \
         patch("controllers.auth_controller.create_access_token") as mock_create_token:
        fake_user=MagicMock()
        fake_user.id=1
        fake_user.email="user@example.com"
        fake_user.hashed_password = "hashed_string"

        mock.return_value=fake_user
        mock_verify.return_value=True
        mock_create_token.return_value="mocked_jwt_token_string"

        response = client.post("/auth/login",json={"email":"user@example.com","password":"CorrectPassword123!"})

        assert response.status_code == 200
        json_data = response.json()
        assert "access_token" in json_data
        assert json_data["access_token"] == "mocked_jwt_token_string"
        assert json_data["token_type"] == "bearer"

        mock_verify.assert_called_once_with("CorrectPassword123!","hashed_string")
        mock_create_token.assert_called_once_with(data={"sub":"1"})

        