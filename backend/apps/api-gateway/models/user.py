from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from config.database import Base

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True,index=True)
    email=Column(String,unique=True,index=True,nullable=False)
    hashed_password=Column(String,nullable=False)
    created_at=Column(DateTime,default=lambda:datetime.now(timezone.utc))