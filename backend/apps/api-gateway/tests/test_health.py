import pytest 
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from main import app

client = TestClient(app)

@patch("controllers.health.AIOKafkaProducer")
@patch("controllers.health.redis_client")
@patch("controllers.health.SessionLocal")
def test_health_all_healthy(mock_db_session, mock_redis, mock_kafka_producer):
    mock_db = MagicMock()
    mock_db_session.return_value = mock_db

    mock_redis.ping = MagicMock(return_value=True)

    mock_producer_instance = AsyncMock()
    mock_kafka_producer.return_value = mock_producer_instance

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"] == {
        "api" : "healthy",
        "postgres" : "healthy",
        "redis" : "healthy",
        "kafka" : "healthy"
    }
    mock_db.close.assert_called_once()
    mock_producer_instance.start.assert_called_once()
    mock_producer_instance.stop.assert_called_once()

@patch("controllers.health.AIOKafkaProducer")
@patch("controllers.health.redis_client")
@patch("controllers.health.SessionLocal")
def test_health_postgres_down(mock_db_session, mock_redis, mock_kafka_producer):
    mock_db_session.side_effect = Exception("DB Connection Refused")

    mock_redis.ping = MagicMock(return_value=True)
    mock_kafka_producer.return_value = AsyncMock()

    response = client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["services"]["postgres"] == "unhealthy"
    assert data["services"]["redis"] == "healthy"
    assert data["services"]["kafka"] == "healthy"


@patch("controllers.health.AIOKafkaProducer")
@patch("controllers.health.redis_client")
@patch("controllers.health.SessionLocal")

def test_health_redis_down(mock_db_session, mock_redis, mock_kafka_producer):
    mock_db_session.return_value = MagicMock()

    mock_redis.ping = MagicMock(side_effect=Exception("Redis connection timed out"))

    mock_kafka_producer.return_value = AsyncMock()

    response = client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["services"]["postgres"]=="healthy"
    assert data["services"]["redis"] == "unhealthy"
    assert data["services"]["kafka"] == "healthy"

@patch("controllers.health.AIOKafkaProducer")
@patch("controllers.health.redis_client")
@patch("controllers.health.SessionLocal")
def test_health_kafka_down(mock_db_session, mock_redis, mock_kafka_producer):
    mock_db_session.return_value = MagicMock()
    mock_redis.ping = MagicMock(return_value=True)

    mock_producer_instance = AsyncMock()
    mock_producer_instance.start.side_effect = Exception("Kafka Broker Unavailable")
    mock_kafka_producer.return_value = mock_producer_instance

    response = client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"]=="unhealthy"
    assert data["services"]["postgres"] == "healthy"
    assert data["services"]["redis"] == "healthy"
    assert data["services"]["kafka"] == "unhealthy"