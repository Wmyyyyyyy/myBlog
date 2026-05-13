from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None

class UserOut(BaseModel):
    id: str
    username: str
    email: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_admin: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class MessageResponse(BaseModel):
    message: str

class UserLogin(BaseModel):
    username: str
    password: str
