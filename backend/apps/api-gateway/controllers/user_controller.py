from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from dto.user_dto import UserCreateDTO, UserResponseDTO
from services.user_service import register_user,get_user
from middlewares.auth import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["User Profiles Management"]
)
@router.post(
        "/",
        response_model=UserResponseDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Register New User Account",
        description="Validates uniqueness of credentials, hashes plain-text passwords securely using bcrypt, and provisions a brand new user profile record in the database."
    )
def create_user(
    user_data:UserCreateDTO,
    db:Session=Depends(get_db)
):
    try:
        new_user=register_user(db=db,email=user_data.email,plain_password=user_data.password)
        return new_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.get(
        "/{user_id}",
        response_model=UserResponseDTO,
        summary="Retrieve Authenticated User Profile",
        description="Extracts credentials out of the incoming bearer token context and echoes back the active verified user object profile details. "
        )
def read_user(user_id:int,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    user=get_user(db=db,user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    return user