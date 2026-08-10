import hashlib
from sqlalchemy import delete
from sqlalchemy.orm import Session
from models.refresh_token import RefreshToken
from datetime import datetime, timezone


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(db: Session, user_id: int, token: str, expires_at: datetime) -> RefreshToken:
    new_token = RefreshToken(user_id=user_id, token_hash=_hash(token), expires_at=expires_at)
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token


def get_refresh_token(db: Session, token: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(
        RefreshToken.token_hash == _hash(token),
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).first()


def revoke_refresh_token(db: Session, token: str):
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == _hash(token)).first()
    if db_token:
        db_token.is_revoked = True
        db.commit()


def delete_expired_tokens(db: Session)->int:
    now = datetime.now(timezone.utc)
    statement = delete(RefreshToken).where(RefreshToken.expires_at<now)
    result = db.execute(statement)
    db.commit()
    return result.rowcount
