from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserRoleUpdate(BaseModel):
    role: str

class UserResponse(BaseModel):
    code: int = 200
    user_id: str
    username: str
    email: str
    full_name: str
    role: str
    created_at: Optional[str] = None

class TokenResponse(BaseModel):
    code: int = 200
    message: str
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: dict