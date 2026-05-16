import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.title = "💰 MoneyManagement (MM)"
API_URL = "http://localhost:8000"


# ==================== Helper Functions (ต้องอยู่ก่อน layout) ====================

def _month_thai(month: int) -> str:
    months = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
        "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
        "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    return months[month]


def _get_month_options() -> list[dict]:
    options = []
    now = datetime.now()
    for i in range(12):
        month = now.month - i
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        value = f"{year}-{month:02d}"
        label = f"{_month_thai(month)} {year}"
        options.append({"label": label, "value": value})
    return options


def _build_summary_cards(summary: dict):
    income = summary.get("total_income", 0)
    expense = summary.get("total_expense", 0)
    balance = summary.get("balance", 0)
    count = summary.get("transaction_count", 0)

    return [
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("💰 รายรับ", className="text-muted"),
                html.H3(f"฿{income:,.2f}", className="text-success")
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("💸 รายจ่าย", className="text-muted"),
                html.H3(f"฿{expense:,.2f}", className="text-danger")
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("🏦 คงเหลือ", className="text-muted"),
                html.H3(
                    f"฿{balance:,.2f}",
                    className="text-primary" if balance >= 0 else "text-danger"
                )
            ])
        ]), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("📋 จำนวนรายการ", className="text-muted"),
                html.H3(f"{count} รายการ", className="text-info")
            ])
        ]), width=3),
    ]


def _build_pie_chart(transactions: list) -> go.Figure:
    expenses = [t for t in transactions if t.get("type") == "expense"]

    if not expenses:
        fig = go.Figure()
        fig.add_annotation(text="ไม่มีข้อมูลรายจ่าย")
        return fig

    category_map = {
        None: "อื่นๆ", 1: "อาหาร", 2: "เดินทาง",
        3: "ช้อปปิ้ง", 4: "ค่าบ้าน", 5: "บันเทิง",
        6: "สุขภาพ", 7: "รายรับ", 8: "อื่นๆ"
    }

    df = pd.DataFrame(expenses)
    df["category_name"] = df["category_id"].map(category_map).fillna("อื่นๆ")
    grouped = df.groupby("category_name")["amount"].sum().reset_index()

    fig = px.pie(
        grouped,
        values="amount",
        names="category_name",
        title="รายจ่ายแยกตามหมวดหมู่",
        hole=0.4
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def _build_bar_chart(summary: dict) -> go.Figure:
    fig = go.Figure(data=[
        go.Bar(name="รายรับ", x=["เดือนนี้"],
               y=[summary.get("total_income", 0)], marker_color="green"),
        go.Bar(name="รายจ่าย", x=["เดือนนี้"],
               y=[summary.get("total_expense", 0)], marker_color="red"),
    ])
    fig.update_layout(barmode="group", title="รายรับ vs รายจ่าย")
    return fig


def _build_transaction_table(transactions: list):
    if not transactions:
        return html.P("ไม่พบรายการธุรกรรม", className="text-muted text-center")

    rows = []
    for t in transactions[:50]:
        color = "table-success" if t.get("type") == "income" else ""
        rows.append(html.Tr([
            html.Td(t.get("date", "")),
            html.Td(t.get("description", "")[:40]),
            html.Td(t.get("bank", "-")),
            html.Td(
                f"฿{t.get('amount', 0):,.2f}",
                className="text-success" if t.get("type") == "income" else "text-danger"
            ),
            html.Td("รายรับ" if t.get("type") == "income" else "รายจ่าย")
        ], className=color))

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("วันที่"), html.Th("รายการ"),
                html.Th("ธนาคาร"), html.Th("จำนวน"), html.Th("ประเภท")
            ])),
            html.Tbody(rows)
        ],
        striped=True, hover=True, responsive=True, size="sm"
    )


# ==================== Layout หลัก ====================

app.layout = dbc.Container([

    dbc.Row([
        dbc.Col([
            html.H1("💰 MoneyManagement", className="text-center my-3"),
            html.P("ระบบจัดการการเงินส่วนตัวสำหรับคนไทย",
                   className="text-center text-muted")
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Label("เลือกเดือน"),
            dcc.Dropdown(
                id="month-selector",
                options=_get_month_options(),
                value=datetime.now().strftime("%Y-%m"),
                clearable=False
            )
        ], width=4),
        dbc.Col([
            dbc.Button("🔄 Refresh", id="refresh-btn", color="primary", className="mt-4")
        ], width=2)
    ], className="mb-4"),

    dbc.Row(id="summary-cards", className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 รายจ่ายแยกตามหมวดหมู่"),
                dbc.CardBody([dcc.Graph(id="pie-chart")])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 รายรับ vs รายจ่าย"),
                dbc.CardBody([dcc.Graph(id="bar-chart")])
            ])
        ], width=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📋 รายการธุรกรรมทั้งหมด"),
                dbc.CardBody([html.Div(id="transaction-table")])
            ])
        ])
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📄 อัปโหลด Statement PDF"),
                dbc.CardBody([
                    dcc.Upload(
                        id="upload-pdf",
                        children=html.Div([
                            "ลากไฟล์มาวางที่นี่ หรือ ",
                            html.A("คลิกเพื่อเลือกไฟล์")
                        ]),
                        style={
                            "width": "100%",
                            "height": "80px",
                            "lineHeight": "80px",
                            "borderWidth": "2px",
                            "borderStyle": "dashed",
                            "borderRadius": "10px",
                            "textAlign": "center",
                            "cursor": "pointer"
                        },
                        accept=".pdf"
                    ),
                    html.Div(id="upload-status", className="mt-3")
                ])
            ])
        ])
    ], className="mb-4"),

    dcc.Interval(id="interval", interval=30000, n_intervals=0)

], fluid=True)


# ==================== Callbacks ====================

@callback(
    Output("summary-cards", "children"),
    Output("pie-chart", "figure"),
    Output("bar-chart", "figure"),
    Output("transaction-table", "children"),
    Input("month-selector", "value"),
    Input("refresh-btn", "n_clicks"),
    Input("interval", "n_intervals")
)
def update_dashboard(month, n_clicks, n_intervals):
    try:
        summary_res = requests.get(f"{API_URL}/summary/{month}", timeout=5)
        summary = summary_res.json() if summary_res.status_code == 200 else {}

        tx_res = requests.get(
            f"{API_URL}/transactions",
            params={"month": month},
            timeout=5
        )
        tx_data = tx_res.json() if tx_res.status_code == 200 else {"transactions": []}
        transactions = tx_data.get("transactions", [])

        return (
            _build_summary_cards(summary),
            _build_pie_chart(transactions),
            _build_bar_chart(summary),
            _build_transaction_table(transactions)
        )

    except Exception as e:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text=f"ไม่สามารถโหลดข้อมูลได้: {str(e)}")
        return [], empty_fig, empty_fig, html.P("ไม่พบข้อมูล")


@callback(
    Output("upload-status", "children"),
    Input("upload-pdf", "contents"),
    prevent_initial_call=True
)
def handle_upload(contents):
    if not contents:
        return ""
    try:
        import base64
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        files = {"file": ("statement.pdf", decoded, "application/pdf")}
        res = requests.post(f"{API_URL}/upload/pdf", files=files, timeout=30)

        if res.status_code == 200:
            data = res.json()
            return dbc.Alert(
                f"✅ อัปโหลดสำเร็จ! พบ {data['total_transactions']} รายการ",
                color="success"
            )
        return dbc.Alert(f"❌ เกิดข้อผิดพลาด: {res.text}", color="danger")

    except Exception as e:
        return dbc.Alert(f"❌ เกิดข้อผิดพลาด: {str(e)}", color="danger")


server = app.server

if __name__ == "__main__":
    app.run(debug=True, port=8050)