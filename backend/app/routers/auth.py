import os
import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# JWT token creation
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=4)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# get_db dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# get_current_user dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Decode the JWT and extract the user id
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Look up the user the token belongs to
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


# Register
@router.post("/auth/register", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")

    # Hash password
    password_hash = pwd_context.hash(user_data.password)

    # Create new user instance
    new_user = User(name=user_data.name, email=user_data.email, password_hash=password_hash)

    # Add to db
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# Login
@router.post("/auth/login", response_model=TokenResponse)
def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()

    # Verify user and password
    if not user or not pwd_context.verify(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password incorrect")

    # Create and return token
    access_token = create_access_token({"sub": str(user.user_id)})
    return TokenResponse(access_token=access_token, token_type="bearer")
