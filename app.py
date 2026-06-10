import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Digital Credit Engine", layout="wide")

# -----------------------------
# CONFIGURATION
# -----------------------------

KIBOR = 12.96 / 100

PRODUCTS = {
    "Personal Loan": {"rate": 0.35, "max_tenor": 5, "fee": "PKR 2,500"},
    "Auto Loan": {"rate": KIBOR + 0.05, "max_tenor": 5, "fee": "PKR 8,000"},
    "Home Loan": {"rate": KIBOR + 0.03, "max_tenor": 20, "fee": "PKR 12,000"},
    "Solar Loan": {"rate": KIBOR + 0.05, "max_tenor": 8, "fee": "PKR 5,000"},
    "Business Loan": {"rate": 0.35, "max_tenor": 5, "fee": "TBA"},
}

DBR = {
    "Salaried": 0.40,
    "Self-Employed": 0.50,
    "Businessman": 0.50,
}

BANKS = [
    "Allied Bank Limited (ABL)",
    "Askari Bank Limited",
    "Bank Alfalah Limited",
    "Bank Al Habib Limited",
    "Bank of Punjab (BOP)",
    "Faysal Bank Limited",
    "Habib Bank Limited (HBL)",
    "Habib Metropolitan Bank",
    "JS Bank Limited",
    "MCB Bank Limited",
    "Meezan Bank Limited",
    "National Bank of Pakistan (NBP)",
    "Samba Bank Limited",
    "Silkbank Limited",
    "Soneri Bank Limited",
    "Standard Chartered Bank (Pakistan)",
    "United Bank Limited (UBL)"
]

# -----------------------------
# FUNCTIONS
# -----------------------------

def emi(p, r, n):
    m = r / 12
    if m == 0:
        return p / n
    return p * m * (1 + m) ** n / ((1 + m) ** n - 1)


def loan_from_emi(e, r, n):
    m = r / 12
    return e * ((1 + m) ** n - 1) / (m * (1 + m) ** n)


def schedule(p, r, n, e):
    m = r / 12
    bal = p
    data = []

    for i in range(1, n + 1):
        interest = bal * m
        principal = e - interest
        bal -= principal

        data.append([i, e, principal, interest, max(bal, 0)])

    return pd.DataFrame(data, columns=[
        "Month", "EMI", "Principal", "Markup", "Balance"
    ])

# -----------------------------
# UI
# -----------------------------

st.title("Digital Credit Engine")

st.header("Applicant Information")

c1, c2, c3 = st.columns(3)

name = c1.text_input("Full Name")

cnic = c2.text_input(...)
if cnic and not re.fullmatch(...)

# auto-format attempt (clean + controlled)
if cnic:
    digits = re.sub(r"\D", "", cnic)  # keep only numbers

    if len(digits) > 13:
        digits = digits[:13]

    if len(digits) >= 5:
        formatted = digits[:5] + "-" + digits[5:]
    else:
        formatted = digits

    if len(digits) >= 12:
        formatted = formatted[:13]  # safety cap
        formatted = formatted[:5] + "-" + formatted[5:12] + "-" + formatted[12:]

    cnic = formatted

if cnic and not re.fullmatch(r"\d{5}-\d{7}-\d", cnic):
    c2.error("Format must be 12345-1234567-1")
gender = c3.selectbox("Gender", ["Male", "Female"])

c4, c5, c6 = st.columns(3)

profession = c4.selectbox("Profession", list(DBR.keys()))
income = c5.number_input("Monthly Income (PKR)", min_value=0)
experience = c6.number_input("Experience (Years)", min_value=0)

st.header("Banking Relationship")

b1, b2 = st.columns(2)

bank = b1.selectbox("Bank", BANKS)
bank_years = b2.number_input("Relationship Years", min_value=0)

st.header("Loan Product")

product = st.selectbox("Select Product", list(PRODUCTS.keys()))

rate = PRODUCTS[product]["rate"]
max_tenor = PRODUCTS[product]["max_tenor"]

tenor = st.selectbox("Tenor (Years)", list(range(1, max_tenor + 1)))
months = tenor * 12

# -----------------------------
# PURPOSE
# -----------------------------

if product == "Personal Loan":
    purpose = st.selectbox(
        "Purpose",
        ["Domestic", "Travel", "Marriage", "Education", "Other"]
    )
    if purpose == "Other":
        purpose = st.text_input("Specify Purpose")
else:
    purpose = st.text_input("Purpose")

# -----------------------------
# ASSET LOGIC
# -----------------------------

asset = 0
equity = 0

if product in ["Auto Loan", "Home Loan", "Solar Loan"]:
    st.header("Asset Details")
    asset = st.number_input("Asset Value (PKR)", min_value=0)

    if product == "Auto Loan":
        equity = st.slider("Equity %", 30, 50, 30)
    elif product in ["Home Loan", "Solar Loan"]:
        equity = st.slider("Equity %", 20, 50, 20)

# -----------------------------
# CALCULATION
# -----------------------------

if st.button("Calculate Eligibility"):

    dbr_limit = DBR[profession]
    max_emi = income * dbr_limit

    max_loan_dbr = loan_from_emi(max_emi, rate, months)

    asset_loan = asset * (1 - equity / 100) if product in ["Auto Loan", "Home Loan", "Solar Loan"] else max_loan_dbr

    approved = min(max_loan_dbr, asset_loan)

    emi_value = emi(approved, rate, months)
    total = emi_value * months
    markup = total - approved

    dbr_actual = emi_value / income if income else 0

    # -----------------------------
    # OUTPUT
    # -----------------------------

    st.success(f"Max loan as per DBR: PKR {max_loan_dbr:,.0f}")

    c1, c2, c3 = st.columns(3)

    c1.metric("Approved Loan", f"PKR {approved:,.0f}")
    c2.metric("Monthly EMI", f"PKR {emi_value:,.0f}")
    c3.metric("DBR", f"{dbr_actual*100:.2f}%")

    st.write("Status:", "Eligible" if dbr_actual <= dbr_limit else "Not Eligible")

    st.subheader("Summary")
    st.write("Total Repayment:", f"PKR {total:,.0f}")
    st.write("Markup:", f"PKR {markup:,.0f}")

    # -----------------------------
    # AMORTIZATION
    # -----------------------------

    st.subheader("Amortization Schedule")

    df = schedule(approved, rate, months, emi_value)
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download Schedule",
        df.to_csv(index=False),
        "schedule.csv",
        "text/csv",
        key="dl1"
    )

    # -----------------------------
    # ENDNOTES
    # -----------------------------

    st.subheader("Bank Notes")

    st.info(f"DBR Limit: {dbr_limit*100:.0f}%")
    st.info(f"Processing Fee: {PRODUCTS[product]['fee']}")

    if product == "Personal Loan":
        st.info("Rate: 35% amortized")
    elif product == "Auto Loan":
        st.info("Rate: KIBOR + 5%")
    elif product == "Home Loan":
        st.info("Rate: KIBOR + 3%")
    elif product == "Solar Loan":
        st.info("Rate: KIBOR + 5%")
    elif product == "Business Loan":
        st.info("Rate: 35% amortized (same as personal loan)")
