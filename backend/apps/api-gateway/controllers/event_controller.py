from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from dto.event_dto import EventCreateDTO,EventResponseDTO
from services import event_service
from config.database import get_db
from middlewares.auth import get_current_user

router = APIRouter(prefix="/events",tags=["Events"])

@router.post("/",status_code=status.HTTP_202_ACCEPTED,response_model=EventResponseDTO)
async def create_event(
    event_in: EventCreateDTO,
    db: Session= Depends(get_db),
    current_user: dict= Depends(get_current_user)
):
    
    event= await event_service.create_and_publish_event(
        db=db,
        user_id=int(current_user.get("sub")),
        event_type=event_in.event_type,
        source=event_in.source,
        payload=event_in.payload
    )
    return event
