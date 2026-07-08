import pytest  
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

@patch("controllers.analytics_controller.analytics_service.get_all_event_counters")
def test_get_all_analytics(mock_get_all):
    mock_get_all.return_value = {
        "USER_LOGIN" : 15,
        "PURCHASE" : 3
    }
    response = client.get("/analytics/")

    assert response.status_code == 200
    data = response.json()
    assert data["USER_LOGIN"] == 15
    assert data["PURCHASE"] == 3

@patch("controllers.analytics_controller.analytics_service.get_event_counter")
def test_get_event_analytics_found(mock_get_one):
    mock_get_one.return_value =42

    response = client.get("/analytics/USER_LOGIN")

    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "USER_LOGIN"
    assert data["count"] == 42
    mock_get_one.assert_called_once_with("USER_LOGIN")

@patch("controllers.analytics_controller.analytics_service.get_event_counter")
def test_get_event_analytics_zero(mock_get_one):
    mock_get_one.return_value = 0

    response = client.get("/analytics/UNKNOWN_EVENT")

    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "UNKNOWN_EVENT"
    assert data["count"] == 0
    mock_get_one.assert_called_once_with("UNKNOWN_EVENT")
    