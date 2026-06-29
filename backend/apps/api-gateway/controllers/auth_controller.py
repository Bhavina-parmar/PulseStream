from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dto.auth_dto import LoginDTO, TokenResponseDTO 
from middlewares.auth import verify_password
from repositories.user_repository import get_user_by_email
from config.database import get_db
from middlewares.auth import create_access_token

router = APIRouter(prefix="/auth",tags=["Authentication"])

@router.post("/login",response_model=TokenResponseDTO)
def login(payload:LoginDTO,db:Session=Depends(get_db)):
    user=get_user_by_email(db,user_email=payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    is_password_correct=verify_password(payload.password,user.hashed_password)
    if not is_password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    token_data={"sub":str(user.id)}
    access_token=create_access_token(data=token_data)
    return TokenResponseDTO(access_token=access_token,token_type="bearer")



