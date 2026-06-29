import re
from repositories.analytics_repository import KNOWN_EVENT_TYPES

def validate_password(value: str) -> str:
    if len(value) < 6:
        raise ValueError("Password must be at least 6 characters")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character")
    return value

def validate_event_type(value: str) -> str:
    upper = value.upper()
    if upper not in KNOWN_EVENT_TYPES:
        raise ValueError(f"event_type must be one of {KNOWN_EVENT_TYPES}")
    return upper

def validate_source(value: str) -> str:
    if not value or not value.strip():
        raise ValueError("source must not be blank")
    return value.strip()

def validate_payload(value: dict) -> dict:
    if not value:
        raise ValueError("payload must not be empty")
    return value
