from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import os
from pathlib import Path
from datetime import datetime

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
from api.routes import router as auth_router
from line_bot.webhook import router as line_router
from ai.advisor import get_ai_advice, read_slip_image
from ai.predictor import predict_next_month
from dashboard.app import app as dash_app

# สร้าง FastAPI App
app = FastAPI(
    title="MoneyManagement (MM)",
    description="ระบบจัดการการเงินส่วนตัวสำหรับคนไทย",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Dash App ที่ /dashboard
app.mount("/dashboard", WSGIMiddleware(dash_app.server))

# Include Routers
app.include_router(auth_router)
app.include_router(line_router)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ MMI Server เริ่มต้นสำเร็จ")
    print("📖 API Docs: http://localhost:8000/docs")
    print("📊 Dashboard: http://localhost:8000/dashboard")


@app.get("/")
def root():
    return {
        "message": "💰 MoneyManagement (MM) API",
        "status": "running",
        "version": "1.0.0",
        "dashboard": "/dashboard",
        "docs": "/docs"
    }


@app.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    categories = get_categories(db)
    return {
        "categories": [
            {"id": c.id, "name": c.name, "name_th": c.name_th, "icon": c.icon}
            for c in categories
        ]
    }


@app.get("/transactions")
def list_transactions(
    user_id: int = 1,
    month: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    transactions = get_transactions(db, user_id=user_id, month=month, category_id=category_id)
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
def remove_transaction(transaction_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    success = delete_transaction(db, transaction_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="ไม่พบรายการธุรกรรม")
    return {"message": "ลบรายการสำเร็จ"}


@app.patch("/transactions/{transaction_id}/category")
def change_category(transaction_id: int, category_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    transaction = update_transaction_category(db, transaction_id, user_id, category_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="ไม่พบรายการธุรกรรม")
    return {"message": "อัปเดตหมวดหมู่สำเร็จ"}


@app.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    bank: Optional[str] = None,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF เท่านั้น")

    temp_path = UPLOAD_DIR / file.filename
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        transactions = parse_statement(str(temp_path), bank)
        if not transactions:
            raise HTTPException(status_code=400, detail="ไม่พบรายการธุรกรรมในไฟล์")

        saved = []
        for tx in transactions:
            category = get_category_by_name(db, tx["category"])
            category_id = category.id if category else None
            saved_tx = create_transaction(
                db=db, user_id=user_id, date=tx["date"],
                description=tx["description"], amount=tx["amount"],
                type=tx["type"], bank=tx.get("bank"), category_id=category_id
            )
            saved.append(saved_tx)

        return {"message": "อ่าน Statement สำเร็จ", "total_transactions": len(saved), "bank": bank or "Auto Detect"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            os.remove(temp_path)


@app.post("/upload/slip")
async def upload_slip(file: UploadFile = File(...), user_id: int = 1, db: Session = Depends(get_db)):
    try:
        image_bytes = await file.read()
        slip_data = read_slip_image(image_bytes)

        category = get_category_by_name(db, categorize(slip_data.get("to_name", "")))
        category_id = category.id if category else None

        date_str = slip_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        tx_date = datetime.strptime(date_str, "%Y-%m-%d")

        saved = create_transaction(
            db=db, user_id=user_id, date=tx_date,
            description=f"โอนเงินให้ {slip_data.get('to_name', 'ไม่ระบุ')}",
            amount=slip_data.get("amount", 0), type="expense",
            bank=slip_data.get("from_bank"), category_id=category_id
        )

        return {"message": "บันทึก Slip สำเร็จ", "transaction_id": saved.id, "slip_data": slip_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary/{month}")
def monthly_summary(month: str, user_id: int = 1, db: Session = Depends(get_db)):
    try:
        return get_monthly_summary(db, user_id, month)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/budget")
def add_budget(user_id: int = 1, category_id: int = 1, amount: float = 0, month: str = "", db: Session = Depends(get_db)):
    budget = create_budget(db, user_id, category_id, amount, month)
    return {"message": "ตั้งงบประมาณสำเร็จ", "budget_id": budget.id}


@app.get("/budget/{month}")
def list_budgets(month: str, user_id: int = 1, db: Session = Depends(get_db)):
    budgets = get_budgets(db, user_id, month)
    return {
        "budgets": [
            {"id": b.id, "category_id": b.category_id, "amount": b.amount, "month": b.month}
            for b in budgets
        ]
    }


@app.get("/ai/advice/{month}")
def ai_advice(month: str, user_id: int = 1, db: Session = Depends(get_db)):
    return get_ai_advice(db, user_id, month)


@app.get("/ai/predict")
def ai_predict(user_id: int = 1, db: Session = Depends(get_db)):
    return predict_next_month(db, user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)