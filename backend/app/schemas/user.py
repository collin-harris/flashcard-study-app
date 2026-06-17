from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
