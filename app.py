import streamlit as st
import pandas as pd
import joblib

# =========================
# LOAD MODEL
# =========================

model = joblib.load("loan_model.pkl")
model_columns = joblib.load("loan_model_columns.pkl")


# =========================
# PAGE CONFIGURATION
# =========================

st.set_page_config(
    page_title="Loan Eligibility Predictor",
    page_icon="🏦",
    layout="centered"
)

st.title("🏦 Loan Eligibility Predictor")
st.write("Enter the applicant details to predict loan eligibility.")


# =========================
# USER INPUTS
# =========================

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


# =========================
# PREDICTION
# =========================

if st.button("Predict Loan Eligibility"):

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