from datetime import datetime
from sqlalchemy import Column,Integer, String, JSON, DateTime
from config.database import Base

class Event(Base):
    __tablename__="events"

    id=Column(Integer,primary_key=True,index=True)
    event_type=Column(String, nullable=False)
    user_id=Column(Integer,nullable=False)
    source=Column(String, nullable=False)
    payload=Column(JSON, nullable=False)
    status= Column(String, default="PENDING",nullable=False)
    created_at=Column(DateTime,default=datetime.utcnow,nullable=False)
    processed_at=Column(DateTime ,nullable=True)