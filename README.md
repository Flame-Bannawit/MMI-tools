# 💰 MoneyManagement (MM)

> **"จัดการเงินง่าย เข้าใจได้ทุกคน"**

MoneyManagement (MM) คือ Web Application สำหรับจัดการการเงินส่วนตัว ที่ช่วยวิเคราะห์พฤติกรรมการใช้เงินจาก Statement ธนาคาร และให้คำแนะนำด้วย AI พร้อม Line Bot ที่อ่าน Slip โอนเงินอัตโนมัติ

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green?logo=fastapi)
![Dash](https://img.shields.io/badge/Dash-Plotly-lightblue?logo=plotly)
![SQLite](https://img.shields.io/badge/SQLite-Local_DB-orange?logo=sqlite)
![Docker](https://img.shields.io/badge/Docker-Deploy-blue?logo=docker)
![Render](https://img.shields.io/badge/Render-Live-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| 📊 Dashboard | [mmi-dashboard.onrender.com](https://mmi-dashboard.onrender.com) |
| 📖 API Docs | [moneymanagement-tools.onrender.com/docs](https://moneymanagement-tools.onrender.com/docs) |
| 📱 Line Bot | @MMI Tools `@690ajaaj` |

---

## ✨ Features

- 📄 **PDF Parser** — อ่าน Statement ธนาคารอัตโนมัติ (KBank, SCB, Bangkok Bank)
- 📸 **Slip Reader** — อ่านรูป Slip โอนเงินด้วย Gemini Vision AI
- 🗂️ **Auto Categorize** — จัดหมวดหมู่รายจ่ายอัตโนมัติ (อาหาร, เดินทาง, ช้อปปิ้ง ฯลฯ)
- 📊 **Dashboard** — กราฟรายรับ-รายจ่าย Pie Chart + Bar Chart + ตารางรายการ
- 🎯 **Budget Tracking** — ตั้ง Budget และติดตามการใช้จ่าย
- 🤖 **AI Advisor** — วิเคราะห์พฤติกรรมและแนะนำวิธีประหยัด (Gemini AI)
- 📈 **Prediction** — ทำนายยอดใช้จ่ายเดือนถัดไป
- 🤖 **Line Bot** — Forward Slip → บันทึกอัตโนมัติ + สรุปรายเดือน
- 🔐 **JWT Auth** — ระบบ Login แยกข้อมูลแต่ละผู้ใช้
- 📤 **Export** — ดาวน์โหลดรายงานเป็น PDF / Excel

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Backend | FastAPI + Uvicorn |
| Database | SQLite + SQLAlchemy + Alembic |
| PDF Parser | pdfplumber |
| Data | Pandas + openpyxl |
| AI / Vision | Gemini AI (google-genai) |
| Dashboard | Dash + Plotly + Bootstrap |
| Line Bot | Line Messaging API v3 + httpx |
| Auth | JWT + Bcrypt |
| DevOps | Docker |
| Deploy | Render (API + Dashboard แยก Service) |

---

## 📁 Project Structure

```
MoneyManagement/
├── core/
│   ├── parser.py           # อ่าน PDF Statement (KBank, SCB, BBL)
│   ├── categorizer.py      # จัดหมวดหมู่รายจ่ายอัตโนมัติ
│   └── analyzer.py         # วิเคราะห์ข้อมูล
├── database/
│   ├── models.py           # Database Schema
│   ├── crud.py             # CRUD Operations
│   └── db.py               # Database Connection + Seed
├── api/
│   ├── routes.py           # Auth API (Register/Login/JWT)
│   └── schemas.py          # Pydantic Models
├── dashboard/
│   └── app.py              # Dash Web Dashboard
├── ai/
│   ├── advisor.py          # Gemini AI Advisor + Slip Reader
│   └── predictor.py        # ML ทำนายยอดรายเดือน
├── line_bot/
│   └── webhook.py          # Line Webhook Handler
├── notifications/
│   └── line_notify.py      # Line Reply Messages
├── tests/
│   ├── test_parser.py
│   ├── test_categorizer.py
│   └── test_api.py
├── main.py                 # FastAPI Entry Point
├── dashboard_server.py     # Dash Entry Point
├── Dockerfile
├── render.yaml
├── requirements.txt
└── .env.example
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker (optional)
- Gemini API Key ([aistudio.google.com](https://aistudio.google.com))
- Line Messaging API Key ([developers.line.me](https://developers.line.me))

### Installation

**1. Clone Repository**

```bash
git clone https://github.com/yourusername/MoneyManagement.git
cd MoneyManagement
```

**2. สร้าง Virtual Environment**

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
source venv/Scripts/activate
```

**3. ติดตั้ง Dependencies**

```bash
pip install -r requirements.txt
```

**4. ตั้งค่า Environment Variables**

```bash
cp .env.example .env
```

แก้ไขไฟล์ `.env`

```env
GEMINI_API_KEY=your_gemini_api_key
LINE_CHANNEL_TOKEN=your_line_channel_token
LINE_CHANNEL_SECRET=your_line_channel_secret
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///./mmi.db
```

**5. รัน API Server**

```bash
python main.py
```

**6. รัน Dashboard (Terminal ใหม่)**

```bash
python dashboard_server.py
```

เปิด Browser
- API Docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8050`

---

### 🐳 Run with Docker

```bash
docker build -t moneymanagement .
docker run -p 8000:8000 --env-file .env moneymanagement
```

---

## 📱 Line Bot Commands

| คำสั่ง | ผลลัพธ์ |
|--------|---------|
| ส่งรูป Slip | บันทึกรายการอัตโนมัติ |
| `สรุป` | สรุปรายรับ-รายจ่ายเดือนนี้ |
| `สรุปวันนี้` | รายการใช้จ่ายวันนี้ |
| `help` | แสดงคำสั่งทั้งหมด |

---

## 🏦 รองรับธนาคาร

| ธนาคาร | PDF Statement | Slip Image |
|--------|--------------|-----------|
| KBank (กสิกรไทย) | ✅ | ✅ |
| SCB (ไทยพาณิชย์) | ✅ | ✅ |
| Bangkok Bank (กรุงเทพ) | ✅ | ✅ |
| ธนาคารอื่นๆ | 🔄 Coming Soon | ✅ |

---

## 📊 Roadmap

- [x] Phase 1 — Core Engine (PDF Parser + Database)
- [x] Phase 2 — Dashboard (Web UI + กราฟ)
- [x] Phase 3 — AI Advisor (Gemini AI)
- [x] Phase 4 — Deploy (Render + Docker + JWT Auth)
- [x] Phase 5 — Line OA + Slip Bot
- [ ] Phase 6 — Email Parser (Auto ดึง Email ธนาคาร)
- [ ] Phase 7 — Mobile App (Flutter)
- [ ] Phase 8 — Open Banking API

---

## ⚠️ ข้อจำกัด

- ไม่สามารถดึงข้อมูลธนาคาร Real-time อัตโนมัติได้
- ไม่สามารถโอนเงินหรือทำธุรกรรมใดๆ ได้
- ไม่ใช่ที่ปรึกษาการเงินหรือการลงทุน
- Version แรกรองรับการใช้งานผ่าน Web Browser และ Line Bot เท่านั้น

---

## 📄 License

[MIT](LICENSE)

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

---

> Built with ❤️ using Python, FastAPI, Dash, and Gemini AI
