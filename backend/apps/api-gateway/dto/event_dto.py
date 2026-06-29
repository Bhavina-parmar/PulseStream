from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from validators import validate_event_type, validate_source, validate_payload

class EventCreateDTO(BaseModel):
    event_type: str
    source: str
    payload: dict

    @field_validator("event_type")
    @classmethod
    def check_event_type(cls, v): return validate_event_type(v)

    @field_validator("source")
    @classmethod
    def check_source(cls, v): return validate_source(v)

    @field_validator("payload")
    @classmethod
    def check_payload(cls, v): return validate_payload(v)

class EventResponseDTO(BaseModel):
    id: int
    event_type: str
    user_id: int
    source: str
    status: str
    created_at: datetime
    model_config=ConfigDict(from_attributes=True)
