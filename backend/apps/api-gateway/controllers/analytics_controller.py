from fastapi import APIRouter
from services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/")
def get_all_analytics():
    return analytics_service.get_all_event_counters()

@router.get("/{event_type}")
def get_event_analytics(event_type: str):
    return {"event_type": event_type, "count": analytics_service.get_event_counter(event_type.upper())}
