from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from .models import Base, Category
import os

load_dotenv()

# ดึง Database URL จาก .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mmi.db")

# สร้าง Engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # จำเป็นสำหรับ SQLite
)

# สร้าง Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """สร้างตารางทั้งหมดในฐานข้อมูล"""
    Base.metadata.create_all(bind=engine)
    _seed_categories()


def get_db():
    """Dependency สำหรับ FastAPI — คืน Session แล้วปิดอัตโนมัติ"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _seed_categories() -> None:
    """เพิ่มหมวดหมู่เริ่มต้นถ้ายังไม่มีในฐานข้อมูล"""
    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            default_categories = [
                Category(name="food",          name_th="อาหาร",        icon="🍔"),
                Category(name="transport",     name_th="เดินทาง",      icon="🚗"),
                Category(name="shopping",      name_th="ช้อปปิ้ง",     icon="🛍️"),
                Category(name="utilities",     name_th="ค่าบ้าน",      icon="🏠"),
                Category(name="entertainment", name_th="บันเทิง",      icon="🎮"),
                Category(name="health",        name_th="สุขภาพ",       icon="💊"),
                Category(name="income",        name_th="รายรับ",       icon="💰"),
                Category(name="other",         name_th="อื่นๆ",        icon="📦"),
            ]
            db.add_all(default_categories)
            db.commit()
    finally:
        db.close()