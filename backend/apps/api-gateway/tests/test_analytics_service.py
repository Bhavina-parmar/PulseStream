from unittest.mock import patch
from services.analytics_service import get_event_counter, get_all_event_counters

@patch("services.analytics_service.analytics_repository.get_counter")
def test_get_event_counter(mock_get_counter):
    mock_get_counter.return_value = 5
    result = get_event_counter("USER_LOGIN")
    assert result == 5

@patch("services.analytics_service.analytics_repository.get_all_counters")
def test_get_all_event_counters(mock_get_all):
    mock_get_all.return_value = {"USER_LOGIN": 5, "PURCHASE": 3}
    result = get_all_event_counters()
    assert result == {"USER_LOGIN": 5, "PURCHASE": 3}

