import asyncio
import json
import logging
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer
from prometheus_client import Counter,start_http_server
from config.database import SessionLocal
from config.settings import settings
from kafka.topics import USER_EVENTS_TOPIC, DLQ_TOPIC
from kafka.producer import publish_event
from repositories import event_repository, analytics_repository
from websocket import ws_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EventWorker")

EVENTS_PROCESSED_TOTAL=Counter(
    "worker_events_processed_total",
    "Total number of kafka events processed successfully.",
    ["event_type"]
)
EVENTS_FAILED_TOTAL=Counter(
    "worker_events_failed_total",
    "Total number of kafka events that exhausted retries and moves to DLQ.",
    ["event_type"]
)

async def process_event(msg):
    db=SessionLocal()
    try:
        payload_str=msg.value.decode('utf-8')
        event_data=json.loads(payload_str)

        event_id= event_data.get("id")
        event_type= event_data.get("event_type")

        if not event_type:
            logger.error("Skipping event processing: Missing 'event_type' in payload.")
            return 
        
        for attempt in range(3):
            try:
                logger.info(f"Consumed event -> ID: {event_id} | Type:{event_type}")

                if not event_id:
                    logger.warning("Received event payload missing an 'id' field.")
                    break

                updated_event = event_repository.update_event_status(
                    db=db,
                    event_id=event_id,
                    status="PROCESSED",
                    processed_at=datetime.now(timezone.utc)
                )
                logger.info(f"Database sync success: Event {event_id} status updated to PROCESSED.")

                new_count = await asyncio.to_thread(analytics_repository.increment_counter, event_type)

                broadcast_payload={
                    "event_type":event_type,
                    "current_count":new_count,
                    "processed_at":datetime.now(timezone.utc).isoformat()
                }
                await ws_manager.broadcast(broadcast_payload)

                EVENTS_PROCESSED_TOTAL.labels(event_type=event_type).inc()

                logger.info(f"Successfully processed and broadcasted event '{event_type}'.")
                break
                
                
            except Exception as e:
                db.rollback()

                attempt_num=attempt+1
                logger.warning(f"Attempt {attempt_num} failed processing event '{event_type}': {str(e)}")

                if attempt<2:
                    delay=2**attempt
                    logger.info(f"Backing off. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All 3 attempts failed. Dropping event processing for '{event_type}'.")
                    try:
                        event_data["dlq_reason"]=str(e)
                        event_data["dlq_failed_at"]=datetime.now(timezone.utc).isoformat()

                        await publish_event(DLQ_TOPIC,event_data)
                        logger.info(f"Successfully quarantined event to DLQ topic :{DLQ_TOPIC}")
                        
                        event_repository.update_event_status(
                            db=db,
                            event_id=event_id,
                            status="FAILED",
                            processed_at=datetime.now(timezone.utc)
                        )

                        EVENTS_FAILED_TOTAL.labels(event_type=event_type).inc()
                    except Exception as dlq_error:
                        logger.critical(f"CRITICAL: Failed to write event to DLQ! Data loss warning:{dlq_error}")


    except json.JSONDecodeError:
        logger.error(f"Failed to parse incoming message value as JSON: {msg.value}")
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
    finally:
        db.close()

async def run_consumer():
    logger.info("Initializing Kafka Consumer...")

    start_http_server(8001)
    logger.info("Prometheus worker metrics server listening natively on port 8001")
    
    consumer = AIOKafkaConsumer(
        USER_EVENTS_TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="event-workers",
        auto_offset_reset="earliest"
    )
    await consumer.start()
    logger.info(f"Worker connected! Listening continuously on topic '{USER_EVENTS_TOPIC}'....")
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
