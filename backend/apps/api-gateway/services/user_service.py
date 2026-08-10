from typing import List
from sqlalchemy.orm import Session
from models.user import User
from repositories.user_repository import create_user, get_user_by_id, get_user_by_email, get_all_users as fetch_all_users
from middlewares.auth import hash_password
import logging 

logger =logging.getLogger(__name__)

def register_user(db: Session, email: str, plain_password: str):
    existing_user = get_user_by_email(db,user_email=email)
    if existing_user:
        logger.warning(f"Registration failed: Email'{email}' already exists.")
        raise ValueError("Email already registered")
    hashed_password = hash_password(plain_password)
    new_user = create_user(db=db, email=email,hashed_password=hashed_password)
    logger.info(f"User Successfully registered with ID: {new_user.id} and Email:{new_user.email}")
    return new_user

def get_user(db:Session,user_id:int):
    return get_user_by_id(db=db,user_id=user_id)

def get_all_users(db: Session) -> List[User]:
    return fetch_all_users(db=db)


   