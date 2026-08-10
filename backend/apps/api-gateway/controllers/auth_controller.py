from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from middlewares.auth import verify_password, create_access_token, create_refresh_token
from repositories.user_repository import get_user_by_email
from repositories.refresh_token_repository import create_refresh_token as save_refresh_token, get_refresh_token, revoke_refresh_token
from config.database import get_db
from dto.auth_dto import RefreshRequestDTO, RefreshResponseDTO, LoginDTO

router = APIRouter(prefix="/auth", tags=["Identity & Access Management"])

@router.post(
        "/login",
        response_model=RefreshResponseDTO,
        summary="Generate OAuth2 Access Token",
        description="Verifies plaintext from parameters against securely recorded password hashes. Returns a signed JWT token string upon successful credential verification."
        )
def login(
    payload: LoginDTO,
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, user_email=payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token,expires_at = create_refresh_token()
    save_refresh_token(db=db,user_id=user.id,token=refresh_token,expires_at=expires_at)
    return RefreshResponseDTO(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=RefreshResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Rotate Refresh Token & Issue Access Token",
    description=(
        "Validates the incoming refresh token, revokes it (token rotation), "
        "and returns a fresh short-lived JWT access token along with a new refresh token."
    )
)
def refresh_token(
    payload: RefreshRequestDTO,
    db: Session= Depends(get_db)
):
    db_token = get_refresh_token(db, token=payload.refresh_token)
    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    
    revoke_refresh_token(db, token=payload.refresh_token)
    
    access_token = create_access_token(data={"sub": str(db_token.user_id), "role": db_token.user.role})
    new_refresh_token, expires_at = create_refresh_token()
    save_refresh_token(db=db, user_id=db_token.user_id, token=new_refresh_token, expires_at=expires_at)
    
    return RefreshResponseDTO(access_token=access_token, refresh_token=new_refresh_token)

@router.post("/logout", status_code=status.HTTP_200_OK, summary="Revoke Refresh Token",
    description="Revokes the provided refresh token, effectively logging the user out.")
def logout(payload: RefreshRequestDTO, db: Session = Depends(get_db)):
    revoke_refresh_token(db, token=payload.refresh_token)
    return {"status": "success", "message": "Logged out successfully"}