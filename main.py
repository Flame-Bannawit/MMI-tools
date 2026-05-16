from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import os
from pathlib import Path

from database.db import init_db, get_db
from database.crud import (
    create_transaction,
    get_transactions,
    get_transaction_by_id,
    update_transaction_category,
    delete_transaction,
    get_categories,
    get_category_by_name,
    get_monthly_summary,
    create_budget,
    get_budgets
)
from core.parser import parse_statement
from core.categorizer import categorize, get_category_thai

# สร้าง FastAPI App
app = FastAPI(
    title="MoneyManagement (MM)",
    description="ระบบจัดการการเงินส่วนตัวสำหรับคนไทย",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# โฟลเดอร์เก็บไฟล์ Upload
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """สร้างฐานข้อมูลเมื่อเริ่มต้น Server"""
    init_db()
    print("✅ MMI Server เริ่มต้นสำเร็จ")
    print("📖 API Docs: http://localhost:8000/docs")


# ==================== Health Check ====================

@app.get("/")
def root():
    """Health Check"""
    return {
        "message": "💰 MoneyManagement (MM) API",
        "status": "running",
        "version": "1.0.0"
    }


# ==================== Categories ====================

@app.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """ดึงหมวดหมู่ทั้งหมด"""
    categories = get_categories(db)
    return {
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "name_th": c.name_th,
                "icon": c.icon
            }
            for c in categories
        ]
    }


# ==================== Transactions ====================

@app.get("/transactions")
def list_transactions(
    user_id: int = 1,
    month: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """ดึงรายการธุรกรรมทั้งหมด"""
    transactions = get_transactions(
        db,
        user_id=user_id,
        month=month,
        category_id=category_id
    )
    return {
        "transactions": [
            {
                "id": t.id,
                "date": t.date.strftime("%Y-%m-%d"),
                "description": t.description,
                "amount": t.amount,
                "type": t.type,
                "bank": t.bank,
                "category_id": t.category_id,
            }
            for t in transactions
        ],
        "total": len(transactions)
    }


@app.delete("/transactions/{transaction_id}")
def remove_transaction(
    transaction_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """ลบรายการธุรกรรม"""
    success = delete_transaction(db, transaction_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="ไม่พบรายการธุรกรรม")
    return {"message": "ลบรายการสำเร็จ"}


@app.patch("/transactions/{transaction_id}/category")
def change_category(
    transaction_id: int,
    category_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """เปลี่ยนหมวดหมู่ของรายการธุรกรรม"""
    transaction = update_transaction_category(db, transaction_id, user_id, category_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="ไม่พบรายการธุรกรรม")
    return {"message": "อัปเดตหมวดหมู่สำเร็จ"}


# ==================== Upload PDF ====================

@app.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    bank: Optional[str] = None,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """อัปโหลดและอ่าน PDF Statement"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF เท่านั้น")

    # บันทึกไฟล์ชั่วคราว
    temp_path = UPLOAD_DIR / file.filename
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # อ่าน PDF
        transactions = parse_statement(str(temp_path), bank)

        if not transactions:
            raise HTTPException(status_code=400, detail="ไม่พบรายการธุรกรรมในไฟล์")

        # บันทึกลง Database
        saved = []
        for tx in transactions:
            category = get_category_by_name(db, tx["category"])
            category_id = category.id if category else None

            saved_tx = create_transaction(
                db=db,
                user_id=user_id,
                date=tx["date"],
                description=tx["description"],
                amount=tx["amount"],
                type=tx["type"],
                bank=tx.get("bank"),
                category_id=category_id
            )
            saved.append(saved_tx)

        return {
            "message": f"อ่าน Statement สำเร็จ",
            "total_transactions": len(saved),
            "bank": bank or "Auto Detect"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # ลบไฟล์ชั่วคราวหลัง Parse เสร็จ
        if temp_path.exists():
            os.remove(temp_path)


# ==================== Summary ====================

@app.get("/summary/{month}")
def monthly_summary(
    month: str,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """สรุปรายรับ-รายจ่ายรายเดือน format: YYYY-MM"""
    try:
        summary = get_monthly_summary(db, user_id, month)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Budget ====================

@app.post("/budget")
def add_budget(
    user_id: int = 1,
    category_id: int = 1,
    amount: float = 0,
    month: str = "",
    db: Session = Depends(get_db)
):
    """ตั้งงบประมาณ"""
    budget = create_budget(db, user_id, category_id, amount, month)
    return {"message": "ตั้งงบประมาณสำเร็จ", "budget_id": budget.id}


@app.get("/budget/{month}")
def list_budgets(
    month: str,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """ดึงงบประมาณทั้งหมดของเดือน"""
    budgets = get_budgets(db, user_id, month)
    return {
        "budgets": [
            {
                "id": b.id,
                "category_id": b.category_id,
                "amount": b.amount,
                "month": b.month
            }
            for b in budgets
        ]
    }


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

from ai.advisor import get_ai_advice, read_slip_image
from ai.predictor import predict_next_month

@app.get("/ai/advice/{month}")
def ai_advice(
    month: str,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """ขอคำแนะนำจาก AI"""
    result = get_ai_advice(db, user_id, month)
    return result


@app.get("/ai/predict")
def ai_predict(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """ทำนายยอดเดือนถัดไป"""
    result = predict_next_month(db, user_id)
    return result


@app.post("/upload/slip")
async def upload_slip(
    file: UploadFile = File(...),
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """อัปโหลดรูป Slip โอนเงิน"""
    try:
        image_bytes = await file.read()
        slip_data = read_slip_image(image_bytes)

        from core.categorizer import categorize
        category = get_category_by_name(db, categorize(slip_data.get("to_name", "")))
        category_id = category.id if category else None

        date_str = slip_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        tx_date = datetime.strptime(date_str, "%Y-%m-%d")

        saved = create_transaction(
            db=db,
            user_id=user_id,
            date=tx_date,
            description=f"โอนเงินให้ {slip_data.get('to_name', 'ไม่ระบุ')}",
            amount=slip_data.get("amount", 0),
            type="expense",
            bank=slip_data.get("from_bank"),
            category_id=category_id
        )

        return {
            "message": "บันทึก Slip สำเร็จ",
            "transaction_id": saved.id,
            "slip_data": slip_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))