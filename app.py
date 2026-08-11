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
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}

h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
    color: #f5f5f5 !important;
}

/* Fix invisible input fields */
input, textarea {
    color: #000000 !important;
    background-color: #ffffff !important;
    border-radius: 8px !important;
}

div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #000000 !important;
    border-radius: 8px !important;
}

.stButton > button {
    background: linear-gradient(90deg, #ff8008, #ffc837);
    color: #000000;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    padding: 0.6em 1.5em;
    transition: 0.3s;
}

.stButton > button:hover {
    transform: scale(1.03);
    box-shadow: 0px 0px 12px rgba(255,200,55,0.6);
}

.auth-card {
    background: rgba(255, 255, 255, 0.08);
    padding: 2rem;
    border-radius: 16px;
    backdrop-filter: blur(6px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.tagline {
    text-align: center;
    font-size: 1.1rem;
    color: #ffd479 !important;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)
# =========================
# LOGIN / SIGNUP PAGE
# =========================

def auth_screen():
    st.markdown("<h1 style='text-align:center;'>🏦 Loan Eligibility Predictor</h1>", unsafe_allow_html=True)
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
    st.markdown(f"### 👤 {st.session_state.username}")
    st.caption("Welcome back!")
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

st.markdown("<h1 style='text-align:center;'>🏦 Loan Eligibility Predictor</h1>", unsafe_allow_html=True)
st.markdown("<div class='tagline'>Enter applicant details below to check loan eligibility instantly</div>", unsafe_allow_html=True)

# ... rest of your existing code (USER INPUTS, PREDICTION section) stays unchanged below this point
