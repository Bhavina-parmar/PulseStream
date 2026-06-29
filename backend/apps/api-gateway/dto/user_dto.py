from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime
from validators import validate_password

class UserCreateDTO(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v): return validate_password(v)

class UserResponseDTO(BaseModel):
    id: int
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)