import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from config.settings import settings
from config.logger import logger
from repositories import refresh_token_repository, user_repository
from middlewares.auth import create_access_token

def generate_refresh_token(db: Session, user_id: int)-> str:
    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    refresh_token_repository.create_refresh_token(
        db=db,
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    return token

def refresh_access_token(db:Session, refresh_token:str)-> str:
    token_record = refresh_token_repository.get_refresh_token(db=db, token=refresh_token)

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    if token_record.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    current_time = datetime.now(timezone.utc)
    token_expire =  token_record.expires_at
    if token_expire.tzinfo is None:
        token_expire = token_expire.replace(tzinfo=timezone.utc)

    if token_expire < current_time:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Refresh token has expired"
        )
    user = user_repository.get_user_by_id(db=db, user_id=token_record.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "User associated with the refresh token not found"
        )
    new_access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user_id": user.id
    }

def revoke_refresh_token(db: Session, refresh_token: str):
    refresh_token_repository.revoke_refresh_token(db=db, token=refresh_token)

def cleanup_expired_tokens(db:Session)->int:
    deleted_count = refresh_token_repository.delete_expired_tokens(db=db)
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired refresh tokens.")
    return deleted_count