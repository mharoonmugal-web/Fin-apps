import streamlit as st
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="Digital Credit Engine", layout="wide")

# -----------------------------
# CONFIGURATION
# -----------------------------

KIBOR = 12.96 / 100
RETIREMENT_AGE = 60

PRODUCTS = {
    "Personal Loan": {"rate": 0.35, "max_tenor": 5, "fee": "PKR 2,500"},
    "Auto Loan": {"rate": KIBOR + 0.05, "max_tenor": 10, "fee": "PKR 8,000"},
    "Home Loan": {"rate": KIBOR + 0.03, "max_tenor": 20, "fee": "PKR 12,000"},
    "Solar Loan": {"rate": KIBOR + 0.05, "max_tenor": 8, "fee": "PKR 5,000"},
    "Business Loan": {"rate": 0.35, "max_tenor": 5, "fee": "TBA"},
}

DBR = {
    "Salaried": 0.40,
    "Self-Employed": 0.50,
    "Businessman": 0.50,
}

# -----------------------------
# CORE FUNCTIONS
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

    return pd.DataFrame(data, columns=["Month", "EMI", "Principal", "Markup", "Balance"])

# -----------------------------
# UI
# -----------------------------

st.title("Digital Credit Engine")

st.header("Applicant Information")

c1, c2, c3 = st.columns(3)

name = c1.text_input("Full Name")

# -----------------------------
# CNIC (STRICT + BLOCKING)
# -----------------------------

cnic_raw = c2.text_input("CNIC (13 digits only)")

cnic_digits = re.sub(r"\D", "", cnic_raw)

cnic_valid = len(cnic_digits) == 13

if cnic_raw:
    if not cnic_valid:
        c2.error("CNIC must be exactly 13 digits (numbers only)")

gender = c3.selectbox("Gender", ["Male", "Female"])

c4, c5, c6 = st.columns(3)

profession = c4.selectbox("Profession", list(DBR.keys()))
income = c5.number_input("Net Monthly Income (PKR)", min_value=0)
experience = c6.number_input("Experience (Years)", min_value=0)

# -----------------------------
# STAFF
# -----------------------------

staff_loan = st.checkbox("Staff Loan")

basic_salary = 0

if staff_loan:
    basic_salary = st.number_input("Basic Salary (PKR)", min_value=0)

# -----------------------------
# PRODUCT
# -----------------------------

st.header("Loan Product")

product = st.selectbox("Select Product", list(PRODUCTS.keys()))

rate_used = PRODUCTS[product]["rate"]
max_tenor = PRODUCTS[product]["max_tenor"]

# -----------------------------
# STAFF HOME LOAN LOGIC (FIXED)
# -----------------------------

max_allowed_tenor = max_tenor

if staff_loan and product == "Home Loan":

    st.subheader("Staff Home Loan Eligibility Inputs")

    dob = st.date_input("Date of Birth")
    doj = st.date_input("Date of Joining")

    today = datetime.today().date()

    retirement_year = dob.year + RETIREMENT_AGE
    remaining_service_years = max(0, retirement_year - today.year)

    max_allowed_tenor = min(25, remaining_service_years)

    st.info(f"Max allowable tenor based on service: {max_allowed_tenor} years")

# -----------------------------
# TENOR
# -----------------------------

tenor = st.selectbox("Tenor (Years)", list(range(1, max_allowed_tenor + 1)))
months = tenor * 12

# -----------------------------
# CALCULATION
# -----------------------------

if st.button("Calculate Eligibility"):

    # CNIC BLOCK
    if not cnic_valid:
        st.error("Invalid CNIC. Please correct before proceeding.")
        st.stop()

    dbr_limit = DBR[profession]
    max_emi = income * dbr_limit

    max_loan_dbr = loan_from_emi(max_emi, rate_used, months)

    # STAFF CAP RULES
    if staff_loan:
        if product == "Personal Loan":
            cap = basic_salary * 8
        elif product == "Auto Loan":
            cap = basic_salary * 50
        elif product == "Home Loan":
            cap = basic_salary * 150
        elif product == "Solar Loan":
            cap = min(3_000_000, max_loan_dbr)
        else:
            cap = max_loan_dbr
    else:
        cap = max_loan_dbr

    approved = cap

    emi_value = emi(approved, rate_used, months)
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

    df = schedule(approved, rate_used, months, emi_value)

    formatted_df = df.copy()

    for col in ["EMI", "Principal", "Markup", "Balance"]:
        formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.0f}")

    st.dataframe(formatted_df, use_container_width=True)

    st.download_button(
        "Download Schedule",
        df.to_csv(index=False),
        "schedule.csv",
        "text/csv",
        key="dl1"
    )

    # -----------------------------
    # END NOTES
    # -----------------------------

    st.subheader("Bank Notes")

    st.info(f"DBR Limit: {dbr_limit*100:.0f}%")
    st.info(f"Processing Fee: {PRODUCTS[product]['fee']}")

    if staff_loan:
        st.info("Staff Pricing: 5% fixed rate applied")
    else:
        st.info(f"Market Rate Applied: {rate_used:.2%}")
