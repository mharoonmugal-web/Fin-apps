import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Alpha Finance - Eligibility Tool", layout="wide")

# -----------------------------
# CONFIGURATION
# -----------------------------

KIBOR = 12.96 / 100

PRODUCTS = {
    "Personal Loan": {"rate": 0.35, "tenor": 5},
    "Auto Loan": {"rate": KIBOR + 0.05, "tenor": 5},
    "Home Loan": {"rate": KIBOR + 0.03, "tenor": 20},
    "Solar Loan": {"rate": KIBOR + 0.05, "tenor": 8},
    "Business Loan": {"rate": KIBOR + 0.05, "tenor": 5},
}

DBR_RULE = {
    "Salaried": 0.40,
    "Self-Employed": 0.50,
    "Businessman": 0.50,
}

BANKS = [
    "HBL", "UBL", "MCB", "ABL", "Bank Alfalah",
    "Meezan Bank", "Bank Al Habib", "Faysal Bank"
]

# -----------------------------
# FUNCTIONS
# -----------------------------

def emi(principal, rate, months):
    r = rate / 12
    if r == 0:
        return principal / months
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)


def loan_from_emi(emi_value, rate, months):
    r = rate / 12
    return emi_value * ((1 + r) ** months - 1) / (r * (1 + r) ** months)


def schedule(principal, rate, months, emi_value):
    r = rate / 12
    bal = principal
    data = []

    for m in range(1, months + 1):
        interest = bal * r
        principal_paid = emi_value - interest
        bal -= principal_paid

        data.append([
            m,
            round(emi_value, 2),
            round(principal_paid, 2),
            round(interest, 2),
            round(max(bal, 0), 2)
        ])

    return pd.DataFrame(data, columns=["Month", "EMI", "Principal", "Markup", "Balance"])


# -----------------------------
# UI HEADER
# -----------------------------

st.title("Alpha Finance - Digital Eligibility Engine")

st.markdown("Banker-style Loan Assessment Tool")

# -----------------------------
# APPLICANT INFO
# -----------------------------

st.header("Applicant Information")

col1, col2, col3 = st.columns(3)

name = col1.text_input("Full Name")
cnic = col2.text_input("CNIC")
gender = col3.selectbox("Gender", ["Male", "Female"])

col4, col5 = st.columns(2)

profession = col4.selectbox("Profession", ["Salaried", "Self-Employed", "Businessman"])
income = col5.number_input("Monthly Income (PKR)", min_value=0)

experience = st.number_input("Experience (Years)", min_value=0, step=1)

# -----------------------------
# BANKING RELATIONSHIP
# -----------------------------

st.header("Banking Relationship")

col6, col7 = st.columns(2)

bank = col6.selectbox("Account Bank", BANKS)
bank_years = col7.number_input("Account Duration (Years)", min_value=0)

# -----------------------------
# PRODUCT SELECTION
# -----------------------------

st.header("Financing Requirement")

product = st.selectbox("Loan Product", list(PRODUCTS.keys()))

rate = PRODUCTS[product]["rate"]
max_tenor = PRODUCTS[product]["tenor"]

tenor_years = st.selectbox("Tenor (Years)", list(range(1, max_tenor + 1)))
months = tenor_years * 12

# -----------------------------
# PURPOSE
# -----------------------------

if product == "Personal Loan":
    purpose = st.selectbox(
        "Purpose",
        ["Domestic Needs", "Travel", "Marriage", "Education", "Entertainment", "Other"]
    )
    if purpose == "Other":
        purpose = st.text_input("Specify Purpose")

else:
    purpose = st.text_input("Specify Purpose")

# -----------------------------
# EQUITY (NON PERSONAL LOAN)
# -----------------------------

asset_value = 0
equity = 0

if product != "Personal Loan":

    st.subheader("Asset Details")

    asset_value = st.number_input("Asset Value (PKR)", min_value=0)

    if product == "Auto Loan":
        equity = st.slider("Equity %", 30, 50, 30)
    elif product == "Solar Loan":
        equity = st.slider("Equity %", 20, 50, 20)
    elif product == "Home Loan":
        equity = st.slider("Equity %", 20, 50, 20)
    else:
        equity = 0

# -----------------------------
# CALCULATIONS
# -----------------------------

if st.button("Calculate Eligibility"):

    dbr_limit = DBR_RULE[profession]
    max_emi = income * dbr_limit

    # PERSONAL LOAN: suggest max loan only
    if product == "Personal Loan":
        loan_amount = loan_from_emi(max_emi, rate, months)
        emi_value = max_emi

    else:
        financing = asset_value * (1 - equity / 100) if asset_value > 0 else 0
        loan_amount = financing
        emi_value = emi(loan_amount, rate, months)

    total_payment = emi_value * months
    markup = total_payment - loan_amount
    dbr = emi_value / income

    eligible = dbr <= dbr_limit

    # -----------------------------
    # OUTPUT
    # -----------------------------

    st.subheader("Assessment Result")

    colA, colB, colC = st.columns(3)

    colA.metric("Loan Amount", f"PKR {loan_amount:,.0f}")
    colB.metric("Monthly EMI", f"PKR {emi_value:,.0f}")
    colC.metric("DBR", f"{dbr*100:.2f}%")

    st.write("**Status:**", "Eligible" if eligible else "Not Eligible")

    st.subheader("Financial Summary")
    st.write("Total Repayment:", f"PKR {total_payment:,.0f}")
    st.write("Total Markup:", f"PKR {markup:,.0f}")

    # -----------------------------
    # AMORTIZATION
    # -----------------------------

    st.subheader("Amortization Schedule")

    df = schedule(loan_amount, rate, months, emi_value)
    st.dataframe(df, use_container_width=True)

    # CSV export
    csv = df.to_csv(index=False)

    st.download_button(
        "Download Schedule (CSV)",
        csv,
        "schedule.csv",
        "text/csv"
    )
