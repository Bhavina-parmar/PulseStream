import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from middlewares.auth import get_current_user
from datetime import datetime

client = TestClient(app)

@patch("controllers.user_controller.register_user")
def test_create_user_success(mock_register):
    fake_user={"id":1,"email":"newuser@example.com","created_at":datetime.now()}
    mock_register.return_value = fake_user

    payload = {"email":"newuser@example.com","password":"Secure123!"}
    response = client.post("/users",json=payload)

    assert response.status_code== 201
    assert response.json()["email"] == "newuser@example.com"


@patch("controllers.user_controller.register_user")
def test_create_user_duplicate_email(mock_register):
    mock_register.side_effect = ValueError("Email already registered")
    
    payload = {"email": "duplicate@example.com","password":"Secure123!"}
    response = client.post("/users",json=payload)

    assert response.status_code == 400
    assert response.json()["status"] == "error"
    assert response.json()["message"] == "Email already registered"


@patch("controllers.user_controller.register_user")
def test_create_user_invalid_password(mock_register):
    mock_register.side_effect = ValueError("Password too short")

    payload = {"email":"user@example.com","password":"Valid123!"}
    response = client.post("/users/",json=payload)

    assert response.status_code == 400
    assert response.json()["status"] == "error"
    assert response.json()["message"] == "Password too short"


@patch("controllers.user_controller.get_user")
def test_get_user_success(mock_get_user):
    app.dependency_overrides[get_current_user] = lambda:{"sub":"42"}

    fake_user = {"id":42, "email": "activeuser@example.com","created_at":datetime.now()}
    mock_get_user.return_value = fake_user

    try:
        response = client.get("/users/42")
        assert response.status_code == 200
        assert response.json()["email"] == "activeuser@example.com"
        #mock_get_user.assert_called_once_with(db=pytest.any_str or MagicMock(), user_id=42)

    finally:
        app.dependency_overrides = {}


@patch("controllers.user_controller.get_user")
def test_get_user_not_found(mock_get_user):
    app.dependency_overrides[get_current_user] = lambda : {"sub":"99"}

    mock_get_user.return_value =None

    try:
        response = client.get("/users/90")
        assert response.status_code == 404
        assert response.json()["status"] == "error"
        assert response.json()["message"] == "User not found"
    finally:
        app.dependency_overrides = {}
