import pdfplumber
import pandas as pd
from datetime import datetime
from typing import Optional
from pathlib import Path
from .categorizer import categorize


# ==================== KBank ====================

def parse_kbank(pdf_path: str) -> list[dict]:
    """
    อ่าน PDF Statement จาก KBank (กสิกรไทย)
    
    Args:
        pdf_path: path ของไฟล์ PDF
        
    Returns:
        list ของรายการธุรกรรม
    """
    transactions = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue

                for row in table[1:]:  # ข้ามแถว Header
                    if not row or len(row) < 4:
                        continue

                    try:
                        date_str = row[0]
                        description = row[1]
                        withdraw = row[2]
                        deposit = row[3]

                        if not date_str or not description:
                            continue

                        # แปลงวันที่
                        date = _parse_date(date_str)
                        if not date:
                            continue

                        # ตรวจสอบว่าเป็นรายรับหรือรายจ่าย
                        if withdraw and withdraw.strip():
                            amount = _parse_amount(withdraw)
                            tx_type = "expense"
                        elif deposit and deposit.strip():
                            amount = _parse_amount(deposit)
                            tx_type = "income"
                        else:
                            continue

                        transactions.append({
                            "date": date,
                            "description": description.strip(),
                            "amount": amount,
                            "type": tx_type,
                            "bank": "KBank",
                            "category": categorize(description)
                        })

                    except Exception:
                        continue

    except Exception as e:
        raise ValueError(f"ไม่สามารถอ่านไฟล์ KBank ได้: {str(e)}")

    return transactions


# ==================== SCB ====================

def parse_scb(pdf_path: str) -> list[dict]:
    """
    อ่าน PDF Statement จาก SCB (ไทยพาณิชย์)
    
    Args:
        pdf_path: path ของไฟล์ PDF
        
    Returns:
        list ของรายการธุรกรรม
    """
    transactions = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue

                for row in table[1:]:
                    if not row or len(row) < 4:
                        continue

                    try:
                        date_str = row[0]
                        description = row[2]
                        withdraw = row[3]
                        deposit = row[4] if len(row) > 4 else None

                        if not date_str or not description:
                            continue

                        date = _parse_date(date_str)
                        if not date:
                            continue

                        if withdraw and withdraw.strip():
                            amount = _parse_amount(withdraw)
                            tx_type = "expense"
                        elif deposit and deposit.strip():
                            amount = _parse_amount(deposit)
                            tx_type = "income"
                        else:
                            continue

                        transactions.append({
                            "date": date,
                            "description": description.strip(),
                            "amount": amount,
                            "type": tx_type,
                            "bank": "SCB",
                            "category": categorize(description)
                        })

                    except Exception:
                        continue

    except Exception as e:
        raise ValueError(f"ไม่สามารถอ่านไฟล์ SCB ได้: {str(e)}")

    return transactions


# ==================== Bangkok Bank ====================

def parse_bbl(pdf_path: str) -> list[dict]:
    """
    อ่าน PDF Statement จาก Bangkok Bank (กรุงเทพ)
    
    Args:
        pdf_path: path ของไฟล์ PDF
        
    Returns:
        list ของรายการธุรกรรม
    """
    transactions = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue

                for row in table[1:]:
                    if not row or len(row) < 4:
                        continue

                    try:
                        date_str = row[0]
                        description = row[1]
                        withdraw = row[2]
                        deposit = row[3]

                        if not date_str or not description:
                            continue

                        date = _parse_date(date_str)
                        if not date:
                            continue

                        if withdraw and withdraw.strip():
                            amount = _parse_amount(withdraw)
                            tx_type = "expense"
                        elif deposit and deposit.strip():
                            amount = _parse_amount(deposit)
                            tx_type = "income"
                        else:
                            continue

                        transactions.append({
                            "date": date,
                            "description": description.strip(),
                            "amount": amount,
                            "type": tx_type,
                            "bank": "BBL",
                            "category": categorize(description)
                        })

                    except Exception:
                        continue

    except Exception as e:
        raise ValueError(f"ไม่สามารถอ่านไฟล์ Bangkok Bank ได้: {str(e)}")

    return transactions


# ==================== Auto Detect ====================

def parse_statement(pdf_path: str, bank: Optional[str] = None) -> list[dict]:
    """
    อ่าน PDF Statement อัตโนมัติ โดยเลือก Parser ตามธนาคาร
    
    Args:
        pdf_path: path ของไฟล์ PDF
        bank: ชื่อธนาคาร (kbank, scb, bbl) ถ้าไม่ระบุจะ Auto Detect
        
    Returns:
        list ของรายการธุรกรรม
    """
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"ไม่พบไฟล์: {pdf_path}")

    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError("รองรับเฉพาะไฟล์ PDF เท่านั้น")

    # เลือก Parser ตามธนาคาร
    if bank:
        bank = bank.lower()
        if bank == "kbank":
            return parse_kbank(pdf_path)
        elif bank == "scb":
            return parse_scb(pdf_path)
        elif bank in ["bbl", "bangkok bank"]:
            return parse_bbl(pdf_path)
        else:
            raise ValueError(f"ไม่รองรับธนาคาร: {bank}")

    # Auto Detect จากเนื้อหาใน PDF
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page_text = pdf.pages[0].extract_text() or ""
            text_lower = first_page_text.lower()

            if "kasikorn" in text_lower or "กสิกร" in text_lower:
                return parse_kbank(pdf_path)
            elif "scb" in text_lower or "ไทยพาณิชย์" in text_lower:
                return parse_scb(pdf_path)
            elif "bangkok bank" in text_lower or "กรุงเทพ" in text_lower:
                return parse_bbl(pdf_path)
            else:
                # ถ้า Detect ไม่ได้ลอง KBank ก่อน
                return parse_kbank(pdf_path)

    except Exception as e:
        raise ValueError(f"ไม่สามารถอ่านไฟล์ PDF ได้: {str(e)}")


def parse_to_dataframe(pdf_path: str, bank: Optional[str] = None) -> pd.DataFrame:
    """
    อ่าน PDF Statement แล้วแปลงเป็น DataFrame
    
    Args:
        pdf_path: path ของไฟล์ PDF
        bank: ชื่อธนาคาร
        
    Returns:
        pandas DataFrame
    """
    transactions = parse_statement(pdf_path, bank)
    if not transactions:
        return pd.DataFrame()
    return pd.DataFrame(transactions)


# ==================== Helper Functions ====================

def _parse_date(date_str: str) -> Optional[datetime]:
    """แปลง string วันที่เป็น datetime รองรับหลายรูปแบบ"""
    if not date_str:
        return None

    date_str = date_str.strip()

    formats = [
        "%d/%m/%Y",
        "%d/%m/%y",
        "%d-%m-%Y",
        "%d-%m-%y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def _parse_amount(amount_str: str) -> float:
    """แปลง string จำนวนเงินเป็น float"""
    if not amount_str:
        return 0.0

    # ลบ comma และช่องว่าง
    cleaned = amount_str.replace(",", "").replace(" ", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return 0.0