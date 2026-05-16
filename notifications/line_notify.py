from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    ImageMessageContent,
    TextMessageContent
)
import os
from dotenv import load_dotenv

load_dotenv()

configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


def get_line_api():
    """สร้าง Line Messaging API Client"""
    with ApiClient(configuration) as api_client:
        return MessagingApi(api_client)


def reply_text(reply_token: str, text: str) -> None:
    """ตอบกลับข้อความ Text"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)]
            )
        )


def format_slip_reply(slip_data: dict, category: str) -> str:
    """สร้างข้อความตอบกลับเมื่ออ่าน Slip สำเร็จ"""
    return (
        f"✅ บันทึกสำเร็จ!\n"
        f"──────────────────\n"
        f"💸 จำนวน  : ฿{slip_data.get('amount', 0):,.2f}\n"
        f"🏦 จาก     : {slip_data.get('from_bank', 'ไม่ระบุ')}\n"
        f"📤 ไปยัง   : {slip_data.get('to_name', 'ไม่ระบุ')}\n"
        f"🗂️ หมวด   : {category}\n"
        f"📅 วันที่  : {slip_data.get('date', 'ไม่ระบุ')}\n"
        f"──────────────────\n"
        f"แก้หมวดพิมพ์ 'แก้ [หมวด]'"
    )


def format_summary_reply(summary: dict) -> str:
    """สร้างข้อความสรุปรายเดือน"""
    return (
        f"📊 สรุปเดือนนี้\n"
        f"──────────────────\n"
        f"💰 รายรับ  : ฿{summary.get('total_income', 0):,.2f}\n"
        f"💸 รายจ่าย : ฿{summary.get('total_expense', 0):,.2f}\n"
        f"🏦 คงเหลือ : ฿{summary.get('balance', 0):,.2f}\n"
        f"📋 รายการ  : {summary.get('transaction_count', 0)} รายการ\n"
        f"──────────────────"
    )