from google import genai
from sqlalchemy.orm import Session
from database.crud import get_transactions, get_monthly_summary
from core.categorizer import get_category_thai
from datetime import datetime
import os
import json
import io
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_ai_advice(db: Session, user_id: int, month: str) -> dict:
    """วิเคราะห์พฤติกรรมการใช้เงินและให้คำแนะนำด้วย AI"""
    try:
        summary = get_monthly_summary(db, user_id, month)
        transactions = get_transactions(db, user_id=user_id, month=month)

        if not transactions:
            return {
                "insights": ["ไม่พบข้อมูลรายการธุรกรรมในเดือนนี้"],
                "recommendations": ["กรุณาอัปโหลด Statement ก่อนครับ"],
                "saving_tips": []
            }

        tx_summary = _prepare_transaction_summary(transactions)

        prompt = f"""
        วิเคราะห์ข้อมูลการเงินของผู้ใช้เดือน {month} และให้คำแนะนำเป็นภาษาไทย

        สรุปการเงิน:
        - รายรับรวม: ฿{summary['total_income']:,.2f}
        - รายจ่ายรวม: ฿{summary['total_expense']:,.2f}
        - คงเหลือ: ฿{summary['balance']:,.2f}
        - จำนวนรายการ: {summary['transaction_count']} รายการ

        รายจ่ายแยกตามหมวดหมู่:
        {tx_summary}

        กรุณาวิเคราะห์และตอบในรูปแบบนี้เท่านั้น:
        INSIGHTS:
        - insight 1
        - insight 2
        - insight 3

        RECOMMENDATIONS:
        - recommendation 1
        - recommendation 2
        - recommendation 3

        SAVING_TIPS:
        - tip 1
        - tip 2
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return _parse_ai_response(response.text)

    except Exception as e:
        return {
            "insights": [f"ไม่สามารถวิเคราะห์ได้: {str(e)}"],
            "recommendations": ["กรุณาตรวจสอบ Gemini API Key"],
            "saving_tips": []
        }


def read_slip_image(image_bytes: bytes) -> dict:
    """อ่านข้อมูลจากรูป Slip ด้วย Gemini Vision"""
    try:
        import PIL.Image

        image = PIL.Image.open(io.BytesIO(image_bytes))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                image,
                """อ่านข้อมูลจาก Slip โอนเงินนี้
                ตอบเป็น JSON รูปแบบนี้เท่านั้น ไม่ต้องมีข้อความอื่น:
                {
                    "date": "YYYY-MM-DD",
                    "time": "HH:MM",
                    "amount": 0.00,
                    "from_bank": "ชื่อธนาคารต้นทาง",
                    "to_name": "ชื่อผู้รับ",
                    "to_bank": "ชื่อธนาคารปลายทาง",
                    "ref_no": "เลขอ้างอิง"
                }"""
            ]
        )

        content = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(content)

    except Exception as e:
        raise ValueError(f"ไม่สามารถอ่าน Slip ได้: {str(e)}")


def _prepare_transaction_summary(transactions: list) -> str:
    """สรุปรายการธุรกรรมแยกตามหมวดหมู่"""
    category_totals: dict = {}

    for tx in transactions:
        if tx.type == "expense":
            cat = get_category_thai(
                tx.category.name if tx.category else "other"
            )
            category_totals[cat] = category_totals.get(cat, 0) + tx.amount

    lines = []
    for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {cat}: ฿{total:,.2f}")

    return "\n".join(lines) if lines else "ไม่มีข้อมูลรายจ่าย"


def _parse_ai_response(content: str) -> dict:
    """Parse ผลลัพธ์จาก AI"""
    result = {
        "insights": [],
        "recommendations": [],
        "saving_tips": []
    }

    current_section = None

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "INSIGHTS:" in line:
            current_section = "insights"
        elif "RECOMMENDATIONS:" in line:
            current_section = "recommendations"
        elif "SAVING_TIPS:" in line:
            current_section = "saving_tips"
        elif line.startswith("- ") and current_section:
            result[current_section].append(line[2:])

    return result