import streamlit as st
import pandas as pd
import joblib
import json
import hashlib
import os
import random
import string
from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

# Gemini (Google GenAI SDK). Guarded import so the rest of the app keeps
# working even if the package isn't installed yet (e.g. before
# requirements.txt has been redeployed).
try:
    from google import genai
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False

# =========================
# AUTH CONFIG
# =========================

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = hash_password(password)
    save_users(users)
    return True, "Account created successfully."

def login_user(username, password):
    users = load_users()
    if username not in users:
        return False, "Username not found."
    if users[username] != hash_password(password):
        return False, "Incorrect password."
    return True, "Login successful."

# =========================
# SESSION STATE INIT
# =========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "application_id" not in st.session_state:
    st.session_state.application_id = None

st.set_page_config(
    page_title="Loan Eligibility Predictor",
    page_icon="🏦",
    layout="centered"
)

# =========================
# GLOBAL THEME / CSS
# =========================

st.markdown("""
<style>
/* ===== Bank Color Palette =====
   Powder Blue : #B3DEF8
   Blue Gray   : #58A1D3
   Classic Blue: #0F4C81
   Blue Slate  : #022C50
   Midnight    : #06172E
================================ */

.stApp {
    background: linear-gradient(135deg, #06172E, #022C50, #0F4C81, #022C50, #06172E);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

header[data-testid="stHeader"] {
    background: #06172E !important;
}

header[data-testid="stHeader"] * {
    color: #B3DEF8 !important;
}

div[data-testid="stDecoration"] {
    display: none !important;
}

/* Entrance animations */
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
    100% { transform: translateY(0px); }
}

@keyframes pulseGlow {
    0% { box-shadow: 0 0 0 0 rgba(88, 161, 211, 0.5); }
    70% { box-shadow: 0 0 0 12px rgba(88, 161, 211, 0); }
    100% { box-shadow: 0 0 0 0 rgba(88, 161, 211, 0); }
}

h1 {
    animation: fadeInDown 0.9s ease-out;
    display: inline-block;
}

.tagline {
    animation: fadeInUp 1s ease-out;
}

.auth-card {
    animation: fadeInUp 0.8s ease-out;
}

/* Floating bank emoji inside the title */
.bank-icon {
    display: inline-block;
    animation: float 3s ease-in-out infinite;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #06172E, #0F4C81);
    border-right: 1px solid #58A1D3;
}

h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, span, div {
    color: #B3DEF8;
}

h1 {
    color: #ffffff !important;
}

/* Fix invisible input fields */
input, textarea {
    color: #06172E !important;
    background-color: #ffffff !important;
    border-radius: 8px !important;
    border: 1px solid #58A1D3 !important;
}

div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #06172E !important;
    border-radius: 8px !important;
    border: 1px solid #58A1D3 !important;
}

div[data-baseweb="select"] span {
    color: #06172E !important;
}

/* Dropdown popover menu (the list that opens when you click a selectbox) */
ul[data-baseweb="menu"] {
    background-color: #ffffff !important;
    border: 1px solid #58A1D3 !important;
}

ul[data-baseweb="menu"] li,
ul[data-baseweb="menu"] li div,
ul[data-baseweb="menu"] li span {
    background-color: #ffffff !important;
    color: #06172E !important;
    -webkit-text-fill-color: #06172E !important;
}

ul[data-baseweb="menu"] li:hover,
ul[data-baseweb="menu"] li:hover div,
ul[data-baseweb="menu"] li:hover span {
    background-color: #B3DEF8 !important;
    color: #06172E !important;
    -webkit-text-fill-color: #06172E !important;
}

ul[data-baseweb="menu"] li[aria-selected="true"],
ul[data-baseweb="menu"] li[aria-selected="true"] div,
ul[data-baseweb="menu"] li[aria-selected="true"] span {
    background-color: #58A1D3 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.stButton > button {
    background: linear-gradient(90deg, #0F4C81, #58A1D3);
    color: #ffffff !important;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    padding: 0.6em 1.5em;
    transition: 0.3s;
    width: 100%;
    animation: pulseGlow 2.5s infinite;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #58A1D3, #B3DEF8);
    color: #06172E !important;
    transform: scale(1.02);
    box-shadow: 0px 0px 14px rgba(179,222,248,0.6);
}

.auth-card {
    background: rgba(179, 222, 248, 0.08);
    padding: 2rem;
    border-radius: 16px;
    backdrop-filter: blur(6px);
    border: 1px solid rgba(88, 161, 211, 0.4);
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    margin-top: 1rem;
}

.tagline {
    text-align: center;
    font-size: 1.1rem;
    color: #58A1D3 !important;
    margin-bottom: 1.5rem;
}

.sidebar-username {
    color: #ffffff !important;
    font-weight: 700;
}

.sidebar-caption {
    color: #B3DEF8 !important;
}

.stSuccess {
    background-color: rgba(88, 161, 211, 0.15) !important;
}

.stTabs [data-baseweb="tab"] {
    color: #B3DEF8 !important;
}

.stTabs [aria-selected="true"] {
    color: #ffffff !important;
    border-bottom-color: #58A1D3 !important;
}
</style>
""", unsafe_allow_html=True)


# =========================
# LOGIN / SIGNUP PAGE
# =========================

def auth_screen():
    st.markdown("<h1 style='text-align:center;'><span class='bank-icon'>🏦</span> Loan Eligibility Predictor</h1>", unsafe_allow_html=True)
    st.markdown("<div class='tagline'>Smart, fast & secure loan approval predictions</div>", unsafe_allow_html=True)

    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        login_username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        if st.button("Login", key="login_btn"):
            if not login_username or not login_password:
                st.error("Please fill in both fields.")
            else:
                success, message = login_user(login_username, login_password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        signup_username = st.text_input("Choose a Username", key="signup_username", placeholder="Pick a username")
        signup_password = st.text_input("Choose a Password", type="password", key="signup_password", placeholder="Pick a password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password", placeholder="Re-enter password")
        if st.button("Sign Up", key="signup_btn"):
            if not signup_username or not signup_password:
                st.error("Username and password cannot be empty.")
            elif signup_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                success, message = signup_user(signup_username, signup_password)
                if success:
                    st.success(message + " Please login now.")
                else:
                    st.error(message)

    st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.logged_in:
    auth_screen()
    st.stop()


# =========================
# SIDEBAR - USER INFO / LOGOUT
# =========================

with st.sidebar:
    st.markdown(f"<div class='sidebar-username'>👤 {st.session_state.username}</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-caption'>Welcome back!</div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.result = None
        st.rerun()


# =========================
# LOAD MODEL
# =========================

model = joblib.load("loan_model.pkl")
model_columns = joblib.load("loan_model_columns.pkl")

st.markdown("<h1 style='text-align:center;'><span class='bank-icon'>🏦</span> Loan Eligibility Predictor</h1>", unsafe_allow_html=True)
st.markdown("<div class='tagline'>Enter applicant details below to check loan eligibility instantly</div>", unsafe_allow_html=True)


# =========================
# USER INPUTS
# =========================

st.markdown("<div class='auth-card'>", unsafe_allow_html=True)

# 👤 Applicant Name — for display / report purposes ONLY.
# This value is NEVER sent to the ML model or included in input_data.
applicant_name = st.text_input(
    "👤 Applicant Name",
    value="",
    placeholder="Enter applicant's full name",
    help="Used only to personalize the on-screen result and the PDF report."
)

gender = st.selectbox(
    "Gender",
    ["Female", "Male"]
)

married = st.selectbox(
    "Married",
    ["No", "Yes"]
)

dependents = st.selectbox(
    "Dependents",
    ["0", "1", "2", "3+"]
)

education = st.selectbox(
    "Education",
    ["Not graduate", "Graduate"]
)

self_employed = st.selectbox(
    "Self Employed",
    ["No", "Yes"]
)

applicant_income = st.number_input(
    "Applicant Income",
    min_value=0,
    value=5000
)

coapplicant_income = st.number_input(
    "Coapplicant Income",
    min_value=0.0,
    value=0.0
)

loan_amount = st.number_input(
    "Loan Amount",
    min_value=0.0,
    value=150.0
)

loan_amount_term = st.selectbox(
    "Loan Amount Term",
    [12, 36, 60, 84, 120, 180, 240, 300, 360, 480],
    index=8
)

credit_history = st.selectbox(
    "Credit History",
    [1.0, 0.0],
    format_func=lambda x: "Good" if x == 1.0 else "Not Available"
)

property_area = st.selectbox(
    "Property Area",
    ["Rural", "Semiurban", "Urban"]
)

predict_clicked = st.button("Predict Loan Eligibility")

st.markdown("</div>", unsafe_allow_html=True)


# =========================
# ENCODING (always computed so it's available both for a fresh
# prediction and for the What-If Simulator on every rerun)
# =========================

gender_value = 0 if gender == "Female" else 1
married_value = 0 if married == "No" else 1
dependents_value = {"0": 0, "1": 1, "2": 2, "3+": 3}[dependents]
education_value = 0 if education == "Not graduate" else 1
self_employed_value = 0 if self_employed == "No" else 1
property_area_value = {"Rural": 0, "Semiurban": 1, "Urban": 2}[property_area]


# =========================
# APPLICATION ID GENERATOR
# =========================

def generate_application_id():
    """Auto-generates a unique Application ID, e.g. LP-2026-A7K92M."""
    year = date.today().year
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"LP-{year}-{suffix}"


# =========================
# PDF REPORT GENERATION (ReportLab Platypus)
# =========================

BANK_NAVY = colors.HexColor("#06172E")
BANK_SLATE = colors.HexColor("#022C50")
BANK_BLUE = colors.HexColor("#0F4C81")
BANK_STEEL = colors.HexColor("#58A1D3")
BANK_POWDER = colors.HexColor("#B3DEF8")
STATUS_GREEN = colors.HexColor("#1e8449")
STATUS_RED = colors.HexColor("#c0392b")


def generate_loan_report_pdf(report_data):
    """
    Builds a professional banking-style PDF loan report using ReportLab
    Platypus and returns it as an in-memory BytesIO buffer.

    report_data keys expected:
        application_id, applicant_name, report_date, is_eligible,
        eligibility_score, score_is_probability,
        gender, married, dependents, education, self_employed,
        property_area, credit_history_label,
        applicant_income, coapplicant_income, loan_amount, loan_amount_term
    """

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title="Loan Eligibility Report",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=20, textColor=colors.white, alignment=TA_CENTER,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontSize=10, textColor=BANK_POWDER, alignment=TA_CENTER,
        spaceAfter=0,
    )
    section_heading_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"],
        fontSize=12, textColor=colors.white, spaceBefore=14, spaceAfter=6,
        backColor=BANK_BLUE, leftIndent=6, borderPadding=(6, 6, 6, 6),
    )
    normal_style = ParagraphStyle(
        "ReportNormal", parent=styles["Normal"],
        fontSize=10, textColor=BANK_SLATE, leading=14,
    )
    notice_style = ParagraphStyle(
        "NoticeStyle", parent=styles["Normal"],
        fontSize=8.5, textColor=colors.HexColor("#555555"), leading=12,
    )

    elements = []

    # ---- Header banner ----
    header_table = Table(
        [[Paragraph("🏦 LOAN ELIGIBILITY REPORT", title_style)],
         [Paragraph("Loan Eligibility Predictor &bull; Educational / Informational Report", subtitle_style)]],
        colWidths=[doc.width],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BANK_NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 14),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 14))

    # ---- Application meta info ----
    meta_table = Table(
        [
            ["Application ID:", report_data["application_id"]],
            ["Applicant Name:", report_data["applicant_name"] or "-"],
            ["Report Date:", report_data["report_date"]],
        ],
        colWidths=[45 * mm, doc.width - 45 * mm],
    )
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), BANK_SLATE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)

    # ---- Loan assessment ----
    elements.append(Paragraph("LOAN ASSESSMENT", section_heading_style))

    if report_data["is_eligible"]:
        result_text = "✅ LOAN ELIGIBLE"
        result_color = STATUS_GREEN
    else:
        result_text = "❌ LOAN NOT ELIGIBLE"
        result_color = STATUS_RED

    result_style = ParagraphStyle(
        "ResultStyle", parent=styles["Normal"],
        fontSize=16, textColor=result_color, alignment=TA_CENTER,
        spaceBefore=4, spaceAfter=4,
    )
    result_box = Table([[Paragraph(result_text, result_style)]], colWidths=[doc.width])
    result_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F7FC")),
        ("BOX", (0, 0), (-1, -1), 1, result_color),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(result_box)
    elements.append(Spacer(1, 4))

    # Prediction confidence — ONLY if the model actually supports predict_proba().
    if report_data["score_is_probability"]:
        elements.append(Paragraph(
            f"Model Confidence (Eligibility Score): <b>{report_data['eligibility_score']} / 100</b>",
            normal_style
        ))
    else:
        elements.append(Paragraph(
            "Model Confidence: Not available (this model does not support probability output).",
            normal_style
        ))

    # ---- Applicant details ----
    elements.append(Paragraph("APPLICANT DETAILS", section_heading_style))
    applicant_table = Table(
        [
            ["Gender", report_data["gender"]],
            ["Marital Status", report_data["married"]],
            ["Dependents", report_data["dependents"]],
            ["Education", report_data["education"]],
            ["Self Employed", report_data["self_employed"]],
            ["Property Area", report_data["property_area"]],
            ["Credit History", report_data["credit_history_label"]],
        ],
        colWidths=[60 * mm, doc.width - 60 * mm],
    )
    applicant_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BANK_POWDER),
        ("TEXTCOLOR", (0, 0), (-1, -1), BANK_SLATE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, BANK_STEEL),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(applicant_table)

    # ---- Financial details ----
    elements.append(Paragraph("FINANCIAL DETAILS", section_heading_style))
    financial_table = Table(
        [
            ["Applicant Income", f"₹{report_data['applicant_income']:,}"],
            ["Co-applicant Income", f"₹{report_data['coapplicant_income']:,.0f}"],
            ["Loan Amount", f"₹{report_data['loan_amount']:,.0f}"],
            ["Loan Amount Term", f"{report_data['loan_amount_term']} months"],
        ],
        colWidths=[60 * mm, doc.width - 60 * mm],
    )
    financial_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BANK_POWDER),
        ("TEXTCOLOR", (0, 0), (-1, -1), BANK_SLATE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, BANK_STEEL),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(financial_table)

    # ---- Prediction summary ----
    elements.append(Paragraph("PREDICTION SUMMARY", section_heading_style))
    elements.append(Paragraph(
        f"Based on the applicant and financial details provided, the trained ML model predicts: "
        f"<b>{'Loan Eligible' if report_data['is_eligible'] else 'Loan Not Eligible'}</b>.",
        normal_style
    ))
    if report_data["score_is_probability"]:
        elements.append(Paragraph(
            f"The model's predicted probability of eligibility corresponds to a score of "
            f"<b>{report_data['eligibility_score']} / 100</b>.",
            normal_style
        ))
    elements.append(Spacer(1, 10))

    # ---- Important notice ----
    elements.append(Paragraph("IMPORTANT NOTICE", section_heading_style))
    elements.append(Paragraph(
        "This report contains an ML-based loan eligibility prediction for educational/informational "
        "purposes only. It does not represent final approval or rejection by any bank or financial "
        "institution.",
        notice_style
    ))

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(BANK_SLATE)
        canvas.drawString(18 * mm, 12 * mm, "Loan Eligibility Predictor")
        canvas.drawRightString(
            A4[0] - 18 * mm, 12 * mm,
            f"Application ID: {report_data['application_id']}"
        )
        canvas.restoreState()

    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer


# =========================
# AI LOAN ADVISOR (Gemini)
# =========================
# API key is read ONLY from Streamlit Secrets — never hardcoded, never
# displayed or printed anywhere.

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    GEMINI_API_KEY = None

GEMINI_MODEL = "gemini-2.5-flash"

AI_ADVISOR_PROMPT_TEMPLATE = """You are an AI Loan Advisor helping explain an ML model's loan eligibility prediction to a bank customer. The ML model — not you — made the actual eligibility decision. Your job is only to explain it and offer general suggestions.

Applicant Information:
- Gender: {gender}
- Married: {married}
- Dependents: {dependents}
- Education: {education}
- Self Employed: {self_employed}
- Applicant Income: ₹{applicant_income}
- Coapplicant Income: ₹{coapplicant_income}
- Loan Amount: ₹{loan_amount}
- Loan Amount Term: {loan_amount_term} months
- Credit History: {credit_history}
- Property Area: {property_area}

ML Model Prediction: {prediction_label}

Rules you must follow strictly:
- Never claim that one specific factor definitely caused the prediction. Use phrases like "may have influenced", "could affect", "may indicate".
- Never invent applicant information that wasn't provided above.
- Never guarantee loan approval or guarantee loan rejection.
- Do not make discriminatory assumptions based on gender, marital status, or property area.
- Do not present yourself as making the final loan decision — the ML model and the bank do that.
- Keep the response professional, easy to understand, and avoid risky or misleading financial advice.

Respond using EXACTLY this Markdown structure:

### 🔍 Why did I get this result?
(Explain in simple language why the ML model may have predicted this result.)

### ✅ Positive Factors
(List factors from the applicant's information that may support loan eligibility.)

### ⚠️ Factors to Consider
(List factors that may negatively affect or create uncertainty around the prediction.)

### 💡 Suggestions
(Give 2-4 practical, general suggestions that could potentially improve the applicant's financial profile.)

### 📌 Important Notice
This is an AI-generated explanation based on the provided information and an ML prediction. It is not a final loan approval or rejection by a bank."""


def get_ai_loan_advice(applicant_details, prediction_label, api_key):
    """Sends the applicant details + ML prediction to Gemini and returns
    a plain-language explanation. The ML prediction itself is NOT
    generated here — it is only explained."""

    prompt = AI_ADVISOR_PROMPT_TEMPLATE.format(
        gender=applicant_details["gender"],
        married=applicant_details["married"],
        dependents=applicant_details["dependents"],
        education=applicant_details["education"],
        self_employed=applicant_details["self_employed"],
        applicant_income=applicant_details["applicant_income"],
        coapplicant_income=applicant_details["coapplicant_income"],
        loan_amount=applicant_details["loan_amount"],
        loan_amount_term=applicant_details["loan_amount_term"],
        credit_history=applicant_details["credit_history"],
        property_area=applicant_details["property_area"],
        prediction_label=prediction_label
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    return response.text


# =========================
# PREDICTION
# =========================
#
# IMPORTANT FIX: Streamlit reruns the entire script on every widget
# interaction, and a st.button() only returns True on the exact run
# where it was clicked. The original code nested the score card, the
# What-If Simulator entirely inside `if predict_clicked:` — so the
# moment the user clicked "Simulate", that rerun made `predict_clicked`
# False again and the WHOLE results section (including the simulator
# itself) vanished before it could show anything.
#
# The fix: run the prediction once and persist its results in
# st.session_state. Everything below (score card, simulator) is
# rendered from session_state, so it survives reruns triggered by any
# button inside it.

if predict_clicked:

    input_data = pd.DataFrame({
        "Gender": [gender_value],
        "Married": [married_value],
        "Dependents": [dependents_value],
        "Education": [education_value],
        "Self_Employed": [self_employed_value],
        "ApplicantIncome": [applicant_income],
        "CoapplicantIncome": [coapplicant_income],
        "LoanAmount": [loan_amount],
        "Loan_Amount_Term": [loan_amount_term],
        "Credit_History": [credit_history],
        "Property_Area": [property_area_value]
    })

    # Match column order to training data
    input_data = input_data[model_columns]

    prediction = model.predict(input_data)[0]

    # Eligibility Score (0-100)
    score_is_probability = True
    try:
        probability = model.predict_proba(input_data)[0][1]
        eligibility_score = round(probability * 100)
    except Exception:
        score_is_probability = False
        eligibility_score = 75 if prediction == 1 else 25

    # ---- Application ID: generated ONLY here, on a NEW prediction.
    # Stored in its own st.session_state slot (not inside result, and
    # never regenerated by the PDF button) so repeated PDF downloads
    # for the same prediction always carry the same ID.
    st.session_state.application_id = generate_application_id()

    # Persist everything needed to render the results (and to run the
    # What-If Simulator / PDF report) across future reruns.
    st.session_state.result = {
        "prediction": int(prediction),
        "eligibility_score": eligibility_score,
        "score_is_probability": score_is_probability,
        "applicant_name": applicant_name,
        # Raw display values, snapshotted for the report
        "gender": gender,
        "married": married,
        "dependents": dependents,
        "education": education,
        "self_employed": self_employed,
        "property_area": property_area,
        # Baseline numeric/encoded values (used as the "current" side
        # of the What-If Simulator comparison, and in the report)
        "applicant_income": applicant_income,
        "coapplicant_income": coapplicant_income,
        "loan_amount": loan_amount,
        "loan_amount_term": loan_amount_term,
        "credit_history": credit_history,
    }


# =========================
# RESULTS (rendered from session_state so they persist across reruns
# caused by the Simulate / Explain buttons below)
# =========================

if st.session_state.result is not None:

    r = st.session_state.result

    prediction = r["prediction"]
    eligibility_score = r["eligibility_score"]
    score_is_probability = r["score_is_probability"]

    # Baseline values captured at prediction time
    base_applicant_income = r["applicant_income"]
    base_coapplicant_income = r["coapplicant_income"]
    base_loan_amount = r["loan_amount"]
    base_loan_amount_term = r["loan_amount_term"]
    base_credit_history = r["credit_history"]

    if eligibility_score >= 80:
        score_label = "🟢 Excellent"
        score_color = "#2ecc71"
    elif eligibility_score >= 60:
        score_label = "🟡 Good"
        score_color = "#f1c40f"
    elif eligibility_score >= 40:
        score_label = "🟠 Moderate"
        score_color = "#e67e22"
    else:
        score_label = "🔴 Low"
        score_color = "#e74c3c"

    score_title = "🎯 LOAN ELIGIBILITY SCORE" if score_is_probability else "🎯 MODEL-BASED ELIGIBILITY SCORE"

    # Result
    if prediction == 1:
        st.success("✅ Loan Eligible")
        st.write("Based on the provided information, the applicant is predicted to be eligible for the loan.")
    else:
        st.error("❌ Loan Not Eligible")
        st.write("Based on the provided information, the applicant is predicted to be not eligible for the loan.")

    # Score Card
    st.markdown(f"""
    <div class="auth-card" style="text-align:center; margin-top:1.2rem; border: 1px solid {score_color};">
        <div style="font-weight:700; letter-spacing:1px; color:#B3DEF8; margin-bottom:0.6rem;">
            {score_title}
        </div>
        <div style="font-size:2.4rem; font-weight:800; color:#ffffff;">
            {eligibility_score}<span style="font-size:1.2rem; color:#58A1D3;"> / 100</span>
        </div>
        <div style="font-size:1.1rem; margin-top:0.4rem; color:{score_color}; font-weight:700;">
            {score_label}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(eligibility_score / 100)

    if not score_is_probability:
        st.caption("This model does not support probability output, so the score above is an estimated model-based indicator rather than a true prediction probability.")

    st.markdown(
        "<div style='color:#B3DEF8; font-size:0.9rem; margin-top:0.5rem;'>"
        "This score represents the model's assessment based on the information provided. "
        "It is not a guaranteed bank approval."
        "</div>",
        unsafe_allow_html=True
    )

    # =========================
    # APPLICATION ID + PROFESSIONAL LOAN REPORT
    # =========================

    st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='auth-card' style='text-align:center; padding:1rem;'>"
        f"<div style='font-weight:700; color:#B3DEF8;'>🆔 APPLICATION ID</div>"
        f"<div style='font-size:1.3rem; font-weight:800; color:#ffffff; margin-top:0.3rem;'>"
        f"{st.session_state.application_id}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    generate_report_clicked = st.button("📄 Generate Loan Report", key="generate_report_btn")

    if generate_report_clicked:
        report_data = {
            "application_id": st.session_state.application_id,
            "applicant_name": r["applicant_name"],
            "report_date": date.today().strftime("%d %B %Y"),
            "is_eligible": prediction == 1,
            "eligibility_score": eligibility_score,
            "score_is_probability": score_is_probability,
            "gender": r["gender"],
            "married": r["married"],
            "dependents": r["dependents"],
            "education": r["education"],
            "self_employed": r["self_employed"],
            "property_area": r["property_area"],
            "credit_history_label": "Good" if base_credit_history == 1.0 else "Not Available",
            "applicant_income": base_applicant_income,
            "coapplicant_income": base_coapplicant_income,
            "loan_amount": base_loan_amount,
            "loan_amount_term": base_loan_amount_term,
        }

        pdf_buffer = generate_loan_report_pdf(report_data)

        st.success("✅ Report generated successfully.")
        st.download_button(
            label="⬇️ Download Loan Report (PDF)",
            data=pdf_buffer,
            file_name=f"{st.session_state.application_id}_Loan_Report.pdf",
            mime="application/pdf",
            key="download_report_btn"
        )

    # =========================
    # AI LOAN ADVISOR
    # =========================

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    with st.expander("🤖 AI Loan Advisor", expanded=False):

        st.markdown(
            "<div class='sidebar-caption'>Get a plain-language explanation of the ML model's result, "
            "along with general suggestions. The ML model made the eligibility decision — the AI only "
            "explains it.</div>",
            unsafe_allow_html=True
        )

        if not GENAI_SDK_AVAILABLE:
            st.warning(
                "⚠️ The AI Loan Advisor is temporarily unavailable: the `google-genai` package is not "
                "installed. Add it to requirements.txt and redeploy."
            )
        elif not GEMINI_API_KEY:
            st.warning(
                "⚠️ The AI Loan Advisor is not configured. Add `GEMINI_API_KEY` to your Streamlit "
                "Secrets to enable this feature."
            )
        else:
            get_advice_clicked = st.button("🤖 Get AI Loan Advice", key="ai_advice_btn")

            if get_advice_clicked:
                with st.spinner("Generating AI explanation..."):
                    try:
                        applicant_details = {
                            "gender": r["gender"],
                            "married": r["married"],
                            "dependents": r["dependents"],
                            "education": r["education"],
                            "self_employed": r["self_employed"],
                            "applicant_income": base_applicant_income,
                            "coapplicant_income": base_coapplicant_income,
                            "loan_amount": base_loan_amount,
                            "loan_amount_term": base_loan_amount_term,
                            "credit_history": "Good" if base_credit_history == 1.0 else "Not Available",
                            "property_area": r["property_area"],
                        }
                        prediction_label = "Loan Eligible" if prediction == 1 else "Loan Not Eligible"

                        advice_text = get_ai_loan_advice(applicant_details, prediction_label, GEMINI_API_KEY)

                        st.success("✅ AI explanation generated.")
                        st.markdown("<div class='auth-card' style='margin-top:1rem;'>", unsafe_allow_html=True)
                        st.markdown(advice_text)
                        st.markdown("</div>", unsafe_allow_html=True)

                    except Exception as e:
                        st.error(
                            "🤖 The AI Loan Advisor is temporarily unavailable. Please try again later."
                        )
                        # TEMPORARY DIAGNOSTIC — remove once the issue is found.
                        # This does NOT print your API key, only the SDK's error message.
                        with st.expander("🔧 Debug details (temporary)"):
                            st.code(f"{type(e).__name__}: {e}")

    # =========================
    # EMI + AFFORDABILITY CALCULATOR
    # =========================


    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    with st.expander("💰 EMI + Affordability Calculator", expanded=False):

        st.markdown(
            "<div class='sidebar-caption'>Estimate the monthly installment for this loan and check "
            "how comfortably it fits within the applicant's income.</div>",
            unsafe_allow_html=True
        )

        st.markdown("<div class='auth-card' style='margin-top:1rem;'>", unsafe_allow_html=True)

        emi_col1, emi_col2 = st.columns(2)

        with emi_col1:
            emi_loan_amount = st.number_input(
                "Loan Amount (₹)",
                min_value=0.0,
                value=float(base_loan_amount) * 1000.0 if base_loan_amount else 0.0,
                step=1000.0,
                key="emi_loan_amount",
                help="Enter the loan principal in rupees."
            )
            emi_interest_rate = st.number_input(
                "Interest Rate (% per annum)",
                min_value=0.0,
                max_value=50.0,
                value=8.5,
                step=0.1,
                key="emi_interest_rate"
            )

        with emi_col2:
            emi_tenure_years = st.number_input(
                "Loan Tenure (Years)",
                min_value=1,
                max_value=40,
                value=max(1, round(base_loan_amount_term / 12)) if base_loan_amount_term else 1,
                step=1,
                key="emi_tenure_years"
            )
            emi_monthly_income = st.number_input(
                "Monthly Income (₹)",
                min_value=0.0,
                value=float(base_applicant_income) if base_applicant_income else 0.0,
                step=500.0,
                key="emi_monthly_income"
            )

        calculate_emi_clicked = st.button("💰 Calculate EMI", key="calculate_emi_btn")

        st.markdown("</div>", unsafe_allow_html=True)

        if calculate_emi_clicked:

            # ----- Standard EMI Formula -----
            # EMI = [P x R x (1+R)^N] / [(1+R)^N - 1]
            # P = Principal loan amount
            # R = Monthly interest rate (annual rate / 12 / 100)
            # N = Loan tenure in months

            principal = emi_loan_amount
            monthly_rate = emi_interest_rate / 12 / 100
            tenure_months = int(emi_tenure_years * 12)

            if principal <= 0 or tenure_months <= 0:
                st.warning("⚠️ Please enter a valid loan amount and tenure to calculate EMI.")
            else:
                if monthly_rate == 0:
                    # Zero-interest edge case: EMI is simply principal / tenure
                    emi = principal / tenure_months
                else:
                    emi = (principal * monthly_rate * (1 + monthly_rate) ** tenure_months) / \
                          ((1 + monthly_rate) ** tenure_months - 1)

                total_payment = emi * tenure_months
                total_interest = total_payment - principal

                if emi_monthly_income > 0:
                    emi_to_income_ratio = (emi / emi_monthly_income) * 100
                else:
                    emi_to_income_ratio = None

                # Affordability status based on EMI-to-Income ratio
                if emi_to_income_ratio is None:
                    afford_label = "⚪ Enter monthly income to check affordability"
                    afford_color = "#58A1D3"
                elif emi_to_income_ratio <= 30:
                    afford_label = "🟢 Affordable"
                    afford_color = "#2ecc71"
                elif emi_to_income_ratio <= 50:
                    afford_label = "🟡 Moderate"
                    afford_color = "#f1c40f"
                else:
                    afford_label = "🔴 High EMI Burden"
                    afford_color = "#e74c3c"

                # Results card
                st.markdown("<div class='auth-card' style='margin-top:1rem;'>", unsafe_allow_html=True)
                st.markdown(
                    "<div style='font-weight:700; color:#B3DEF8; margin-bottom:0.6rem;'>📊 EMI Breakdown</div>",
                    unsafe_allow_html=True
                )

                emi_res_col1, emi_res_col2, emi_res_col3 = st.columns(3)
                with emi_res_col1:
                    st.metric("Monthly EMI", f"₹{emi:,.2f}")
                with emi_res_col2:
                    st.metric("Total Interest", f"₹{total_interest:,.2f}")
                with emi_res_col3:
                    st.metric("Total Payment", f"₹{total_payment:,.2f}")

                if emi_to_income_ratio is not None:
                    st.markdown(
                        f"<div style='margin-top:0.8rem; font-size:1rem; color:#B3DEF8;'>"
                        f"EMI-to-Income Ratio: <span style='font-weight:700; color:#ffffff;'>"
                        f"{emi_to_income_ratio:.1f}%</span></div>",
                        unsafe_allow_html=True
                    )
                    st.progress(min(emi_to_income_ratio, 100) / 100)

                st.markdown("</div>", unsafe_allow_html=True)

                # Affordability status card
                st.markdown(f"""
                <div class="auth-card" style="text-align:center; margin-top:1rem; border: 1px solid {afford_color};">
                    <div style="font-weight:700; letter-spacing:1px; color:#B3DEF8; margin-bottom:0.6rem;">
                        AFFORDABILITY STATUS
                    </div>
                    <div style="font-size:1.4rem; font-weight:800; color:{afford_color};">
                        {afford_label}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(
                    "<div style='color:#B3DEF8; font-size:0.9rem; margin-top:0.7rem;'>"
                    "This calculator uses the standard EMI formula for estimation purposes only. "
                    "It does not account for processing fees, taxes, or bank-specific charges."
                    "</div>",
                    unsafe_allow_html=True
                )

    # =========================
    # WHAT-IF LOAN SIMULATOR
    # =========================

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    with st.expander("🔄 What-If Loan Simulator", expanded=False):

        st.markdown(
            "<div class='sidebar-caption'>Adjust the values below to see how changes to the applicant's "
            "financial profile could affect the loan eligibility result.</div>",
            unsafe_allow_html=True
        )

        st.markdown("<div class='auth-card' style='margin-top:1rem;'>", unsafe_allow_html=True)

        loan_term_options = [12, 36, 60, 84, 120, 180, 240, 300, 360, 480]

        sim_col1, sim_col2 = st.columns(2)

        with sim_col1:
            sim_applicant_income = st.number_input(
                "Simulated Applicant Income",
                min_value=0,
                value=int(base_applicant_income),
                key="sim_applicant_income"
            )
            sim_coapplicant_income = st.number_input(
                "Simulated Coapplicant Income",
                min_value=0.0,
                value=float(base_coapplicant_income),
                key="sim_coapplicant_income"
            )
            sim_loan_amount = st.number_input(
                "Simulated Loan Amount",
                min_value=0.0,
                value=float(base_loan_amount),
                key="sim_loan_amount"
            )

        with sim_col2:
            sim_loan_amount_term = st.selectbox(
                "Simulated Loan Amount Term",
                loan_term_options,
                index=loan_term_options.index(base_loan_amount_term),
                key="sim_loan_amount_term"
            )
            sim_credit_history = st.selectbox(
                "Simulated Credit History",
                [1.0, 0.0],
                index=[1.0, 0.0].index(base_credit_history),
                format_func=lambda x: "Good" if x == 1.0 else "Not Available",
                key="sim_credit_history"
            )

        simulate_clicked = st.button("🔄 Simulate", key="simulate_btn")

        st.markdown("</div>", unsafe_allow_html=True)

        if simulate_clicked:

            # Build simulator input using modified values, keeping the
            # non-editable fields (gender, married, etc.) the same as
            # the current main form.
            simulator_data = pd.DataFrame({
                "Gender": [gender_value],
                "Married": [married_value],
                "Dependents": [dependents_value],
                "Education": [education_value],
                "Self_Employed": [self_employed_value],
                "ApplicantIncome": [sim_applicant_income],
                "CoapplicantIncome": [sim_coapplicant_income],
                "LoanAmount": [sim_loan_amount],
                "Loan_Amount_Term": [sim_loan_amount_term],
                "Credit_History": [sim_credit_history],
                "Property_Area": [property_area_value]
            })

            # Match column order to training data
            simulator_data = simulator_data[model_columns]

            # New prediction using the same trained model
            simulated_prediction = model.predict(simulator_data)[0]

            current_label = "✅ Loan Eligible" if prediction == 1 else "❌ Loan Not Eligible"
            simulated_label = "✅ Loan Eligible" if simulated_prediction == 1 else "❌ Loan Not Eligible"

            # Result comparison card
            st.markdown("<div class='auth-card' style='margin-top:1rem;'>", unsafe_allow_html=True)

            result_col1, result_col2 = st.columns(2)
            with result_col1:
                st.markdown("<div style='font-weight:700; color:#B3DEF8;'>CURRENT RESULT</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:1.3rem; margin-top:0.3rem;'>{current_label}</div>", unsafe_allow_html=True)
            with result_col2:
                st.markdown("<div style='font-weight:700; color:#B3DEF8;'>WHAT-IF RESULT</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:1.3rem; margin-top:0.3rem;'>{simulated_label}</div>", unsafe_allow_html=True)

            # Change message
            if simulated_prediction == 1 and prediction == 0:
                st.success("🎉 Your simulated profile shows improved loan eligibility.")
            elif simulated_prediction == 0 and prediction == 1:
                st.warning("⚠️ Your simulated profile shows lower loan eligibility.")
            else:
                st.info("ℹ️ Your simulated result is unchanged.")

            st.markdown("</div>", unsafe_allow_html=True)

            # Field-by-field comparison
            st.markdown("<div class='auth-card' style='margin-top:1rem;'>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight:700; color:#B3DEF8; margin-bottom:0.6rem;'>📊 What Changed</div>", unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Applicant Income", f"₹{sim_applicant_income}", delta=int(sim_applicant_income - base_applicant_income))
            with c2:
                st.metric("Loan Amount", f"₹{sim_loan_amount}", delta=float(sim_loan_amount - base_loan_amount))
            with c3:
                st.metric(
                    "Credit History",
                    "Good" if sim_credit_history == 1.0 else "Not Available",
                    delta="Changed" if sim_credit_history != base_credit_history else "No change"
                )
            with c4:
                st.metric("Loan Term", f"{sim_loan_amount_term} mo", delta=int(sim_loan_amount_term - base_loan_amount_term))

            st.markdown("</div>", unsafe_allow_html=True)

            # Disclaimer
            st.markdown(
                "<div style='color:#B3DEF8; font-size:0.9rem; margin-top:0.7rem;'>"
                "This simulator provides an ML-based prediction only. It does not guarantee actual "
                "loan approval or rejection by a bank."
                "</div>",
                unsafe_allow_html=True
            )

else:
    st.info("ℹ️ Please click **Predict Loan Eligibility** first. A Loan Report can only be generated after a prediction has been made.")



