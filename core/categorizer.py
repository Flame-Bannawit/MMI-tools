from typing import Optional


# คำสำคัญสำหรับจัดหมวดหมู่อัตโนมัติ
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food": [
        # ร้านอาหาร
        "mcdonald", "kfc", "burger", "pizza", "sushi", "shabu", "mk ",
        "ชาบู", "ข้าว", "ก๋วยเตี๋ยว", "ส้มตำ", "หมูกระทะ", "บุฟเฟ่",
        # Delivery
        "grab food", "grabfood", "foodpanda", "lineman", "shopee food",
        # เครื่องดื่ม
        "starbucks", "cafe", "กาแฟ", "ชานม", "บาบิก้า", "ชา", "coffee",
        # ซูเปอร์มาร์เก็ต
        "tops", "villa market", "gourmet",
    ],
    "transport": [
        "grab", "bolt", "uber", "แท็กซี่", "taxi",
        "bts", "mrt", "รถไฟ", "airport rail",
        "น้ำมัน", "ptt", "shell", "esso", "bangchak", "คาลเท็กซ์",
        "แก๊ส", "ที่จอดรถ", "parking", "ทางด่วน", "expressway",
        "วินมอเตอร์ไซค์",
    ],
    "shopping": [
        "shopee", "lazada", "amazon", "jd central",
        "central", "the mall", "siam", "terminal21", "icon siam",
        "uniqlo", "h&m", "zara", "nike", "adidas",
        "bigc", "lotus", "makro", "tesco",
        "it city", "banana it", "jib", "advice",
    ],
    "utilities": [
        "ค่าไฟ", "ค่าน้ำ", "ค่าเน็ต", "อินเตอร์เน็ต", "internet",
        "ais", "dtac", "true", "nt ", "tot ",
        "ค่าเช่า", "ค่าห้อง", "นิติบุคคล",
        "electric", "water", "pea ", "mea ",
    ],
    "entertainment": [
        "netflix", "spotify", "youtube", "disney", "hbo",
        "steam", "playstation", "xbox", "nintendo",
        "โรงหนัง", "sf ", "major ", "cinema",
        "คาราโอเกะ", "บาร์", "bar", "pub", "ผับ",
        "บิลเลียด", "โบว์ลิ่ง", "bowling",
    ],
    "health": [
        "โรงพยาบาล", "hospital", "clinic", "คลินิก",
        "ร้านขายยา", "pharmacy", "boots", "watsons",
        "หมอ", "ทันตแพทย์", "แพทย์",
        "ฟิตเนส", "fitness", "gym", "โยคะ", "yoga",
        "วิตามิน", "vitamin", "supplement",
    ],
    "income": [
        "เงินเดือน", "salary", "โบนัส", "bonus",
        "รับโอน", "รับเงิน", "dividend", "ปันผล",
        "freelance", "ค่าจ้าง",
    ],
}


def categorize(description: str) -> str:
    """
    จัดหมวดหมู่รายการธุรกรรมจากคำอธิบาย
    
    Args:
        description: คำอธิบายรายการธุรกรรม
        
    Returns:
        ชื่อหมวดหมู่ภาษาอังกฤษ เช่น 'food', 'transport'
    """
    if not description:
        return "other"

    text = description.lower().strip()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category

    return "other"


def categorize_with_confidence(description: str) -> dict:
    """
    จัดหมวดหมู่พร้อม Confidence Score
    
    Args:
        description: คำอธิบายรายการธุรกรรม
        
    Returns:
        dict ที่มี category และ confidence
    """
    if not description:
        return {"category": "other", "confidence": 0.0, "matched_keyword": None}

    text = description.lower().strip()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return {
                    "category": category,
                    "confidence": 1.0,
                    "matched_keyword": keyword
                }

    return {"category": "other", "confidence": 0.0, "matched_keyword": None}


def get_category_thai(category_name: str) -> str:
    """แปลงชื่อหมวดหมู่จากอังกฤษเป็นไทย"""
    mapping = {
        "food": "อาหาร",
        "transport": "เดินทาง",
        "shopping": "ช้อปปิ้ง",
        "utilities": "ค่าบ้าน/สาธารณูปโภค",
        "entertainment": "บันเทิง",
        "health": "สุขภาพ",
        "income": "รายรับ",
        "other": "อื่นๆ",
    }
    return mapping.get(category_name, "อื่นๆ")