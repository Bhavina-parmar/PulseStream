import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from models.event import Event
from services.event_service import create_and_publish_event

pytestmark = pytest.mark.asyncio

@patch("services.event_service.event_repository.create_event")
@patch("services.event_service.publish_event",new_callable=AsyncMock)
async def test_create_event_success(mock_publish_event, mock_create_event) -> None:
    mock_db = MagicMock()
    user_id = 42
    event_type ="USER_LOGIN"
    source = "web-client"
    payload = {"ip": "127.0.0.1"}

    fake_event = Event(
        id=101,
        user_id=user_id,
        event_type=event_type,
        source=source,
        payload=payload,
        status="PENDING",
        created_at=datetime.now(timezone.utc)
    )
    mock_create_event.return_value=fake_event
    result = await create_and_publish_event(
        db=mock_db,
        user_id=user_id,
        event_type=event_type,
        source=source,
        payload=payload
    )
    assert result == fake_event
    assert result.id==101

    mock_create_event.assert_called_once_with(
        db=mock_db,
        event_type=event_type,
        user_id=user_id,
        source=source,
        payload=payload
    )
    mock_publish_event.assert_called_once()

@patch("services.event_service.event_repository.create_event")
@patch("services.event_service.publish_event",new_callable=AsyncMock)
async def test_create_event_kafka_failure(mock_publish_event,mock_create_event)->None:
    mock_db=MagicMock()
    user_id = 42
    event_type = "PURCHASE"
    source = "mobile-app"
    payload = {"amount" : 99.99}

    fake_event = Event(
        id=102,
        user_id=user_id,
        event_type=event_type,
        source=source,
        payload=payload,
        status="PENDING",
        created_at=datetime.now(timezone.utc)

    )
    mock_create_event.return_value = fake_event
    mock_publish_event.side_effect = Exception("Kafka connection timeout")
    result=await create_and_publish_event(
        db=mock_db,
        user_id=user_id,
        event_type=event_type,
        source=source,
        payload=payload
    )

    assert result == fake_event
    assert result.id == 102

    mock_create_event.assert_called_once()
    mock_publish_event.assert_called_once()


@patch("services.event_service.event_repository.create_event")
@patch("services.event_service.publish_event", new_callable=AsyncMock)
async def test_create_event_stores_correct_fields(mock_publish_event, mock_create_event):
    mock_db = MagicMock()
    fake_event = Event(
        id=103,
        user_id=101,
        event_type="CUSTOM_ACTION",
        source="mobile-app",
        payload={"feature": "dark_mode"},
        status="PENDING",
        created_at=datetime.now(timezone.utc)
    )
    mock_create_event.return_value = fake_event

    result = await create_and_publish_event(
        db=mock_db,
        user_id=101,
        event_type="CUSTOM_ACTION",
        source="mobile-app",
        payload={"feature": "dark_mode"}
    )

    assert result.user_id == 101
    assert result.event_type == "CUSTOM_ACTION"
    assert result.source == "mobile-app"
    assert result.status == "PENDING"

@patch("services.event_service.event_repository.create_event")
@patch("services.event_service.publish_event", new_callable=AsyncMock)
async def test_create_event_different_types(mock_publish_event, mock_create_event):
    mock_db = MagicMock()
    fake_event = Event(
        id=104,
        user_id=202,
        event_type="PAGE_VIEW",
        source="safari-browser",
        payload={"url": "/home"},
        status="PENDING",
        created_at=datetime.now(timezone.utc)
    )
    mock_create_event.return_value = fake_event

    result = await create_and_publish_event(
        db=mock_db,
        user_id=202,
        event_type="PAGE_VIEW",
        source="safari-browser",
        payload={"url": "/home"}
    )

    assert result.event_type == "PAGE_VIEW"
    assert result.user_id == 202
