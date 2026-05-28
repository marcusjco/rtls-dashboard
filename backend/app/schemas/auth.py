from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: Optional[str]
    username: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
