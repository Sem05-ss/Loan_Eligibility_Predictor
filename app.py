import streamlit as st
import pandas as pd
import joblib
import json
import hashlib
import os

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
# PREDICTION
# =========================

if predict_clicked:

    # Encoding inputs

    gender_value = 0 if gender == "Female" else 1

    married_value = 0 if married == "No" else 1

    dependents_value = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3+": 3
    }[dependents]

    education_value = 0 if education == "Not graduate" else 1

    self_employed_value = 0 if self_employed == "No" else 1

    property_area_value = {
        "Rural": 0,
        "Semiurban": 1,
        "Urban": 2
    }[property_area]

    # Create input dataframe

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

    # Make sure column order is same as training data

    input_data = input_data[model_columns]

    # Prediction

    prediction = model.predict(input_data)[0]

    # Result

    if prediction == 1:
        st.success("✅ Loan Eligible")
        st.write("Based on the provided information, the applicant is predicted to be eligible for the loan.")
    else:
        st.error("❌ Loan Not Eligible")
        st.write("Based on the provided information, the applicant is predicted to be not eligible for the loan.")
