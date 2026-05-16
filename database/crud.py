from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import datetime
from typing import Optional
from . models import User, Transaction, Category, Budget
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== User ====================

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """ดึงข้อมูล User จาก Email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """ดึงข้อมูล User จาก Username"""
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, email: str, password: str) -> User:
    """สร้าง User ใหม่"""
    hashed_password = pwd_context.hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ตรวจสอบ Password"""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== Transaction ====================

def create_transaction(
    db: Session,
    user_id: int,
    date: datetime,
    description: str,
    amount: float,
    type: str,
    bank: Optional[str] = None,
    category_id: Optional[int] = None,
    slip_image_path: Optional[str] = None
) -> Transaction:
    """สร้างรายการธุรกรรมใหม่"""
    transaction = Transaction(
        user_id=user_id,
        date=date,
        description=description,
        amount=amount,
        type=type,
        bank=bank,
        category_id=category_id,
        slip_image_path=slip_image_path
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_transactions(
    db: Session,
    user_id: int,
    month: Optional[str] = None,
    category_id: Optional[int] = None,
    limit: int = 100
) -> list[Transaction]:
    """ดึงรายการธุรกรรมทั้งหมดของ User"""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if month:
        year, m = month.split("-")
        query = query.filter(
            extract("year", Transaction.date) == int(year),
            extract("month", Transaction.date) == int(m)
        )

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    return query.order_by(Transaction.date.desc()).limit(limit).all()


def get_transaction_by_id(db: Session, transaction_id: int, user_id: int) -> Optional[Transaction]:
    """ดึงรายการธุรกรรมตาม ID"""
    return db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()


def update_transaction_category(
    db: Session,
    transaction_id: int,
    user_id: int,
    category_id: int
) -> Optional[Transaction]:
    """อัปเดตหมวดหมู่ของรายการธุรกรรม"""
    transaction = get_transaction_by_id(db, transaction_id, user_id)
    if transaction:
        transaction.category_id = category_id
        db.commit()
        db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction_id: int, user_id: int) -> bool:
    """ลบรายการธุรกรรม"""
    transaction = get_transaction_by_id(db, transaction_id, user_id)
    if transaction:
        db.delete(transaction)
        db.commit()
        return True
    return False


# ==================== Category ====================

def get_categories(db: Session) -> list[Category]:
    """ดึงหมวดหมู่ทั้งหมด"""
    return db.query(Category).all()


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    """ดึงหมวดหมู่จากชื่อ"""
    return db.query(Category).filter(Category.name == name).first()


# ==================== Budget ====================

def create_budget(
    db: Session,
    user_id: int,
    category_id: int,
    amount: float,
    month: str
) -> Budget:
    """สร้างงบประมาณใหม่"""
    budget = Budget(
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        month=month
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_budgets(db: Session, user_id: int, month: str) -> list[Budget]:
    """ดึงงบประมาณทั้งหมดของ User ในเดือนนั้น"""
    return db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.month == month
    ).all()


def get_monthly_summary(db: Session, user_id: int, month: str) -> dict:
    """สรุปรายรับ-รายจ่ายรายเดือน"""
    year, m = month.split("-")
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        extract("year", Transaction.date) == int(year),
        extract("month", Transaction.date) == int(m)
    ).all()

    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expense = sum(t.amount for t in transactions if t.type == "expense")

    return {
        "month": month,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "transaction_count": len(transactions)
    }