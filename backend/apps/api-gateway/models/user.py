from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from config.database import Base
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import relationship, Mapped, mapped_column
from models.refresh_token import RefreshToken

class User(Base):
    __tablename__="users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc)
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )