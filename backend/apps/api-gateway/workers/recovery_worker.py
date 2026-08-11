import asyncio
import logging
from config.database import SessionLocal
from config.logger import setup_logging, logger
from dto.event_dto import EventResponseDTO
from kafka.producer import publish_event, stop_producer
from kafka.topics import USER_EVENTS_TOPIC
from repositories import event_repository

setup_logging()
POLL_INTERVAL_SECONDS = 30

async def recover_pending_events():
    logger.info("Starting recovery worker iteration...")
    with SessionLocal() as db:
        pending_events = event_repository.get_pending_event(db=db, threshold_second=60)
        if not pending_events:
            logger.info("No stranded PENDING events found.")
            return
        logger.info(f"Found {len(pending_events)} PENDING events eligible for recovery.")
        for event in pending_events:
            try:
                event_dto =EventResponseDTO.model_validate(event)
                await publish_event(USER_EVENTS_TOPIC, event_dto.model_dump(mode="json"))

                db.commit()
                logger.info(f"Successfully recovered and published event ID: {event.id}")
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Failed to recover event ID: {event.id}. Reason: {str(e)}",
                    exc_info= True
                )


async def main():
    logger.info("Recovery Worker started. Monitoring PENDING events every 30 seconds.")
    try:
        while True:
            await recover_pending_events()
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("Recovery worker gracefullly stopped.")
    finally:
        await stop_producer()
        logger.info("Recovery worker gracefully stopped.")

if __name__ == "__main__":
    asyncio.run(main())
