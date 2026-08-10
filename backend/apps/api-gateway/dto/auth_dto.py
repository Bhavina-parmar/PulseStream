from pydantic import BaseModel, EmailStr, Field, ConfigDict

class LoginDTO(BaseModel):
    email:EmailStr
    password: str

class TokenResponseDTO(BaseModel):
    access_token:str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Single-use refresh token")
    token_type:str=Field(default="bearer", description="Token authorization type")

class RefreshRequestDTO(BaseModel):
    refresh_token :str = Field(
        ..., 
        description="The current valid refresh token string",
        examples=["dGhpcyBpcyBhIHNlY3VyZSByYW5kb20gdG9rZW4"]
    )

class RefreshResponseDTO(BaseModel):
    access_token: str = Field(
        ...,
        description="Newly generated short-lived JWT access token"
    )
    refresh_token: str = Field(
        ...,
        description="Newly generated single-use refresh token (Token Rotation)"
    )
    token_type: str =Field(
        default= "bearer",
        description = "Token autherization type"
    )
    model_config = ConfigDict(from_attributes=True)
    
