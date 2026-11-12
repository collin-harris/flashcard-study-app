from typing import Annotated
from pydantic import AfterValidator, BaseModel
from pydantic_core import PydanticCustomError

from app.schemas.validators import required_text


def normalize_email(email: str) -> str:
    return email.strip().lower()


# Emails are compared case-insensitively, so they're stored and looked up in
# one normalized form
NormalizedEmail = Annotated[str, AfterValidator(normalize_email)]


PASSWORD_MIN_CHARACTERS = 8
# bcrypt uses only the first 72 bytes of a password and ignores the rest
PASSWORD_MAX_BYTES = 72


def check_new_password(password: str) -> str:
    # Not stripped: spaces are part of a password
    if len(password) < PASSWORD_MIN_CHARACTERS:
        raise PydanticCustomError(
            "password_too_short", f"Password must be at least {PASSWORD_MIN_CHARACTERS} characters."
        )
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise PydanticCustomError(
            "password_too_long",
            "Password is too long. Use at most 72 characters, or fewer if it includes emoji or accented letters.",
        )
    return password


# Registration only. Login takes any password, so accounts created before
# these rules can still log in.
class UserCreate(BaseModel):
    name: Annotated[str, required_text("Name can't be empty.")]
    email: NormalizedEmail
    password: Annotated[str, AfterValidator(check_new_password)]


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
