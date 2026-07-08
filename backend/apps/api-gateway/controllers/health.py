import logging
from fastapi import APIRouter, Response, status
from aiokafka import AIOKafkaProducer
from config.database import SessionLocal
from config.redis import redis_client
from config.settings import settings
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System Health"])


@router.get(
        "/health",
        summary="Deep Dependency Health Sweep",
        description="Sweeps backend connections (PostgreSQL state engine, Redis memory pools, and live AIOKafka broker pipelines) returning a granular status health report array."
        )
async def read_health(response: Response):
    health_status = "healthy"
    services = {
        "api":"healthy",
        "postgres" : "healthy",
        "redis" : "healthy",
        "kafka" : "healthy"
    }
    db=None
    try:
        db=SessionLocal()
        db.execute(text("SELECT 1"))
    except Exception as pg_err:
        logger.error(f"Health check failed for PostgreSQL: {pg_err}")
        services["postgres"]="unhealthy"
        health_status="unhealthy"
    finally:
        if db:
            db.close()

    try:
        redis_client.ping()
    except Exception as redis_err:
        logger.error(f"Health check failed for Redis: {redis_err}")
        services["redis"] = "unhealthy"
        health_status = "unhealthy"

    try:
        producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
        await producer.start()
        await producer.stop()
    except Exception as kafka_err:
        logger.error(f"Health check failed for kafka: {kafka_err}")
        services["kafka"]="unhealthy"
        health_status = "unhealthy"

    if health_status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status" : health_status,
        "services" : services
    }