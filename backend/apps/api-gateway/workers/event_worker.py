import asyncio
import json
import logging
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer
from config.database import SessionLocal
from config.settings import settings
from kafka.topics import USER_EVENTS_TOPIC
from repositories import event_repository, analytics_repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EventWorker")

async def process_event(msg):
    db=SessionLocal()
    try:
        payload_str=msg.value.decode('utf-8')
        event_data=json.loads(payload_str)
        event_id= event_data.get("id")
        event_type= event_data.get("event_type")
        logger.info(f"Consumed event -> ID: {event_id} | Type:{event_type}")
        if event_id:
            updated_event = event_repository.update_event_status(
                db=db,
                event_id=event_id,
                status="PROCESSED",
                processed_at=datetime.now(timezone.utc)
            )
            logger.info(f"Database sync success: Event {event_id} status updated to PROCESSED.")
            if event_type:
                analytics_repository.increment_counter(event_type)
                logger.info(f"Analytics counter incremented for event type: {event_type}")
        else:
            logger.warning("Received event payload missing an 'id' field.")

    except json.JSONDecodeError:
        logger.error(f"Failed to parse incoming message value as JSON: {msg.value}")
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
    finally:
        db.close()

async def run_consumer():
    logger.info("Initializing Kafka Consumer...")
    consumer = AIOKafkaConsumer(
        USER_EVENTS_TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="event-workers",
        auto_offset_reset="earliest"
    )
    await consumer.start()
    logger.info(f"Worker connected! Listening continously on topic '{USER_EVENTS_TOPIC}'....")
    try:
        async for msg in consumer:
            await process_event(msg)
    except Exception as loop_error:
        logger.error(f"Exception encountered in consumer engine: {loop_error}")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer connection stopped cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(run_consumer())
    except KeyboardInterrupt:
        logger.info("Worker stopped manually via keyboard interrupt (ctrl+C). Exiting.")
