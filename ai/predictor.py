from sqlalchemy.orm import Session
from database.crud import get_monthly_summary
from datetime import datetime


def predict_next_month(db: Session, user_id: int) -> dict:
    """ทำนายยอดใช้จ่ายเดือนถัดไปจากข้อมูลย้อนหลัง 3 เดือน"""
    try:
        now = datetime.now()
        monthly_data = []

        for i in range(1, 4):
            month = now.month - i
            year = now.year
            if month <= 0:
                month += 12
                year -= 1
            month_str = f"{year}-{month:02d}"
            summary = get_monthly_summary(db, user_id, month_str)
            if summary["transaction_count"] > 0:
                monthly_data.append(summary)

        if not monthly_data:
            return {
                "predicted_expense": 0,
                "predicted_income": 0,
                "confidence": "ต่ำ",
                "message": "ไม่มีข้อมูลเพียงพอสำหรับการทำนาย"
            }

        avg_expense = sum(d["total_expense"] for d in monthly_data) / len(monthly_data)
        avg_income = sum(d["total_income"] for d in monthly_data) / len(monthly_data)

        next_month = now.month + 1
        next_year = now.year
        if next_month > 12:
            next_month = 1
            next_year += 1

        confidence = "สูง" if len(monthly_data) >= 3 else "ปานกลาง"

        return {
            "predicted_expense": round(avg_expense, 2),
            "predicted_income": round(avg_income, 2),
            "predicted_balance": round(avg_income - avg_expense, 2),
            "next_month": f"{next_year}-{next_month:02d}",
            "based_on_months": len(monthly_data),
            "confidence": confidence,
            "message": f"ทำนายจากข้อมูลย้อนหลัง {len(monthly_data)} เดือน"
        }

    except Exception as e:
        return {
            "predicted_expense": 0,
            "predicted_income": 0,
            "confidence": "ต่ำ",
            "message": f"เกิดข้อผิดพลาด: {str(e)}"
        }