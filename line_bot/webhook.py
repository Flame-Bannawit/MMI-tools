from fastapi import APIRouter, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    MessageEvent,
    ImageMessageContent,
    TextMessageContent
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi
)
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.crud import (
    get_monthly_summary,
    get_transactions,
    get_category_by_name
)
from ai.advisor import read_slip_image
from core.categorizer import categorize, get_category_thai
from notifications.line_notify import reply_text, format_slip_reply, format_summary_reply
from datetime import datetime
import os

router = APIRouter()

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


@router.post("/webhook/line")
async def line_webhook(request: Request):
    """รับ Webhook จาก Line"""
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"status": "ok"}


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    """จัดการรูปภาพ Slip ที่ส่งมา"""
    db = SessionLocal()
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            image_content = line_bot_api.get_message_content(event.message.id)
            image_bytes = image_content.read()

        slip_data = read_slip_image(image_bytes)

        from database.crud import create_transaction
        category_name = categorize(slip_data.get("to_name", ""))
        category = get_category_by_name(db, category_name)
        category_id = category.id if category else None
        category_th = get_category_thai(category_name)

        date_str = slip_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        try:
            tx_date = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            tx_date = datetime.now()

        create_transaction(
            db=db,
            user_id=1,
            date=tx_date,
            description=f"โอนเงินให้ {slip_data.get('to_name', 'ไม่ระบุ')}",
            amount=slip_data.get("amount", 0),
            type="expense",
            bank=slip_data.get("from_bank"),
            category_id=category_id
        )

        reply_text(
            event.reply_token,
            format_slip_reply(slip_data, category_th)
        )

    except Exception as e:
        reply_text(event.reply_token, f"❌ ไม่สามารถอ่าน Slip ได้\n{str(e)}")
    finally:
        db.close()


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    """จัดการข้อความที่พิมพ์มา"""
    db = SessionLocal()
    text = event.message.text.strip().lower()

    try:
        if text in ["สรุป", "summary"]:
            month = datetime.now().strftime("%Y-%m")
            summary = get_monthly_summary(db, user_id=1, month=month)
            reply_text(event.reply_token, format_summary_reply(summary))

        elif text in ["สรุปวันนี้", "today"]:
            month = datetime.now().strftime("%Y-%m")
            transactions = get_transactions(db, user_id=1, month=month)
            today = datetime.now().date()
            today_tx = [
                t for t in transactions
                if t.date.date() == today
            ]
            if today_tx:
                total = sum(t.amount for t in today_tx if t.type == "expense")
                reply_text(
                    event.reply_token,
                    f"📅 วันนี้ใช้จ่ายรวม\n฿{total:,.2f}\nจำนวน {len(today_tx)} รายการ"
                )
            else:
                reply_text(event.reply_token, "ยังไม่มีรายการวันนี้ครับ")

        elif text in ["help", "ช่วยเหลือ", "?"]:
            reply_text(
                event.reply_token,
                "💰 MMI Bot คำสั่งที่ใช้ได้\n"
                "──────────────────\n"
                "📸 ส่งรูป Slip → บันทึกอัตโนมัติ\n"
                "📊 สรุป → สรุปเดือนนี้\n"
                "📅 สรุปวันนี้ → รายการวันนี้\n"
                "❓ help → แสดงคำสั่ง"
            )

        else:
            reply_text(
                event.reply_token,
                "พิมพ์ 'help' เพื่อดูคำสั่งทั้งหมดครับ 😊"
            )

    except Exception as e:
        reply_text(event.reply_token, f"❌ เกิดข้อผิดพลาด: {str(e)}")
    finally:
        db.close()