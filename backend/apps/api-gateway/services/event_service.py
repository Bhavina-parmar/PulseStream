import logging
from sqlalchemy.orm import Session
from repositories import event_repository
from kafka.producer import publish_event
from kafka.topics import USER_EVENTS_TOPIC
from dto.event_dto import EventResponseDTO

logger=logging.getLogger(__name__)

async def create_and_publish_event(db: Session, user_id: int, event_type: str, source: str, payload: dict):
    db_event = event_repository.create_event(
        db=db,
        event_type= event_type,
        user_id= user_id,
        source= source,
        payload= payload
    )

    logger.info(f"Event created in DB -> ID : {db_event.id} | Type: {event_type} | User ID: {user_id}")

    event_dto=EventResponseDTO.model_validate(db_event)
    try: 
        await publish_event(USER_EVENTS_TOPIC,event_dto.model_dump())
    except Exception as kafka_error:
        logger.error(
            f"Failed to publish event {db_event.id} to Kafka topic '{USER_EVENTS_TOPIC}'."
            f"Reason: {str(kafka_error)}"
        )
    return db_event