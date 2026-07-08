import pytest
from datetime import datetime
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from main import app
from middlewares.auth import get_current_user

client = TestClient(app)

@patch("controllers.event_controller.event_service.create_and_publish_event", new_callable=AsyncMock)

def test_create_event_success(mock_create_and_punlish):

    app.dependency_overrides[get_current_user] = lambda : {"sub":"1"}

    fake_event = MagicMock()
    fake_event.id =1
    fake_event.event_type = "USER_LOGIN"
    fake_event.user_id = 1
    fake_event.source = "web-client"
    fake_event.status = "PENDING"
    fake_event.created_at = datetime.now()

    mock_create_and_punlish.return_value = fake_event
    mock_create_and_punlish.side_effect = None

    payload = {
        "event_type" : "USER_LOGIN",
        "source" : "web_client",
        "payload" : {"ip": "127.0.0.1"}
    }

    try:
        response = client.post("/events/",json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["id"]  == 1
        assert data["event_type"] == "USER_LOGIN"
        assert data["status"] == "PENDING"
    
    finally:
        app.dependency_overrides = {}

def test_create_event_unauthorized():
    def mock_unauthorized():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
    
    app.dependency_overrides[get_current_user] =mock_unauthorized

    payload = {
        "event_type" : "USER_LOGIN",
        "source" : "web-client",
        "payload" : {"ip":"127.0.0.1"}
    }

    try:
        response = client.post("/events/", json=payload)
        assert response.status_code == 401

    finally:
        app.dependency_overrides = {}

def test_create_event_invalid_payload():
    app.dependency_overrides[get_current_user] = lambda:{"sub":"1"}
    try:
        response = client.post("/events/", json={"event_type":"USER_LOGIN","source":"web-client","payload":{}})
        assert response.status_code == 422
    finally:
        app.dependency_overrides = {}

