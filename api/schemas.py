from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ==================== User ====================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ==================== Transaction ====================

class TransactionCreate(BaseModel):
    date: datetime
    description: str
    amount: float
    type: str
    bank: Optional[str] = None
    category_id: Optional[int] = None


class TransactionResponse(BaseModel):
    id: int
    date: datetime
    description: str
    amount: float
    type: str
    bank: Optional[str]
    category_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Budget ====================

class BudgetCreate(BaseModel):
    category_id: int
    amount: float
    month: str


class BudgetResponse(BaseModel):
    id: int
    category_id: int
    amount: float
    month: str

    class Config:
        from_attributes = True