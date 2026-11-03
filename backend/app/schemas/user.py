from typing import Annotated
from pydantic import AfterValidator, BaseModel


def normalize_email(email: str) -> str:
    return email.strip().lower()


# Emails are compared case-insensitively, so they're stored and looked up in
# one normalized form
NormalizedEmail = Annotated[str, AfterValidator(normalize_email)]


class UserCreate(BaseModel):
    name: str
    email: NormalizedEmail
    password: str


class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str


class LoginRequest(BaseModel):
    email: NormalizedEmail
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
