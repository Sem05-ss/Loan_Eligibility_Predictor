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
# LOGIN / SIGNUP PAGE
# =========================

def auth_screen():
    st.title("🏦 Loan Eligibility Predictor")
    st.subheader("Please login or sign up to continue")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            success, message = login_user(login_username, login_password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with tab2:
        signup_username = st.text_input("Choose a Username", key="signup_username")
        signup_password = st.text_input("Choose a Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        if st.button("Sign Up"):
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


if not st.session_state.logged_in:
    auth_screen()
    st.stop()
    # =========================
# SIDEBAR - USER INFO / LOGOUT
# =========================

with st.sidebar:
    st.write(f"👤 Logged in as: **{st.session_state.username}**")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# =========================
# LOAD MODEL
# =========================

model = joblib.load("loan_model.pkl")
model_columns = joblib.load("loan_model_columns.pkl")

st.title("🏦 Loan Eligibility Predictor")
st.write("Enter the applicant details to predict loan eligibility.")

# ... rest of your existing code (USER INPUTS, PREDICTION section) stays unchanged below this point
