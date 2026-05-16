from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

from database.db import get_db
from database.crud import (
    get_user_by_email,
    get_user_by_username,
    create_user,
    verify_password
)
from api.schemas import UserCreate, UserResponse, Token

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "changethiskey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 วัน

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ==================== JWT ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """สร้าง JWT Access Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """ดึงข้อมูล User จาก JWT Token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token ไม่ถูกต้องหรือหมดอายุ",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user


# ==================== Auth Routes ====================

@router.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """สมัครสมาชิก"""
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email นี้ถูกใช้แล้ว")

    if get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username นี้ถูกใช้แล้ว")

    user = create_user(db, user_data.username, user_data.email, user_data.password)
    return user


@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """เข้าสู่ระบบ"""
    user = get_user_by_email(db, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email หรือ Password ไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """ดึงข้อมูล User ปัจจุบัน"""
    return current_user