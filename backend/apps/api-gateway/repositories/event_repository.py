from datetime import datetime
from sqlalchemy.orm import Session
from models.event import Event

def create_event(db: Session, event_type: str,user_id: int,source: str,payload: dict)->Event:
    db_event = Event(
        event_type=event_type,
        user_id=user_id,
        source=source,
        payload=payload
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
def update_event_status(db: Session, event_id: int,status: str, processed_at: datetime=None)-> Event:
    db_event = db.query(Event).filter(Event.id==event_id).first()
    if db_event:
        db_event.status=status
        if processed_at:
            db_event.processed_at=processed_at
        db.commit()
        db.refresh(db_event)
    return db_event

