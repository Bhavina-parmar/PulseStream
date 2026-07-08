from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from datetime import datetime
from validators import validate_password

class UserCreateDTO(BaseModel):
    email: EmailStr = Field(
        ...,
        description="A unique, system-wide valid email identifier for account authentication",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="A plain text credential payload that must meet baseline complexity criteria rules",
        examples=["Secure123!"]
    )

    @field_validator("password")
    @classmethod
    def password_strength(cls, v): return validate_password(v)

class UserResponseDTO(BaseModel):
    id: int
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)