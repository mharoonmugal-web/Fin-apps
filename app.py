import streamlit as st
import pandas as pd
import re
from datetime import date

st.set_page_config(page_title="Digital Credit Engine", layout="wide")

# -----------------------------
# CONFIGURATION
# -----------------------------

KIBOR = 12.96 / 100
RETIREMENT_AGE = 60

DBR = {
    "Salaried": 0.40,
    "Self-Employed": 0.50,
    "Businessman": 0.50,
}

PRODUCTS = {
    "Personal Loan": {
        "rate": 0.35,
        "max_tenor": 5,
        "fee": "PKR 2,500",
        "equity": False
    },
    "Auto Loan": {
        "rate": KIBOR + 0.05,
        "max_tenor": 10,
        "fee": "PKR 8,000",
        "equity": True
    },
    "Home Loan": {
        "rate": KIBOR + 0.03,
        "max_tenor": 20,
        "fee": "PKR 12,000",
        "equity": True
    },
    "Solar Loan": {
        "rate": KIBOR + 0.05,
        "max_tenor": 8,
        "fee": "PKR 5,000",
        "equity": True
    },
    "Business Loan": {
        "rate": 0.35,
        "max_tenor": 5,
        "fee": "TBA",
        "equity": False
    }
}

BANKS = [
    "Habib Bank Limited", "United Bank Limited", "MCB Bank",
    "Allied Bank", "Bank Alfalah", "Meezan Bank",
    "Bank Al Habib", "Faysal Bank", "The Bank of Punjab",
    "Askari Bank", "JS Bank", "Soneri Bank"
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
    rows = []

    for i in range(1, n + 1):
        interest = bal * m
        principal = e - interest
        bal -= principal

        rows.append([i, e, principal, interest, max(bal, 0)])

    return pd.DataFrame(rows, columns=["Month", "EMI", "Principal", "Markup", "Balance"])


# -----------------------------
# UI START
# -----------------------------

st.title("Digital Credit Engine")

st.header("Applicant Information")

c1, c2, c3 = st.columns(3)

name = c1.text_input("Full Name")

# -----------------------------
# CNIC (STRICT VALIDATION)
# -----------------------------

cnic_raw = c2.text_input("CNIC (13 digits only)")

cnic_digits = re.sub(r"\D", "", cnic_raw)[:13]
cnic_valid = len(cnic_digits) == 13

if cnic_raw and not cnic_valid:
    c2.error("CNIC must be exactly 13 digits (numbers only)")

gender = c3.selectbox("Gender", ["Male", "Female"])

c4, c5, c6 = st.columns(3)

profession = c4.selectbox("Profession", list(DBR.keys()))
income = c5.number_input("Net Monthly Income (PKR)", min_value=0)
experience = c6.number_input("Experience (Years)", min_value=0)

# -----------------------------
# STAFF LOGIC
# -----------------------------

staff_allowed = (profession == "Salaried")

staff_loan = False
if staff_allowed:
    staff_loan = st.checkbox("Staff Loan")

basic_salary = 0
if staff_loan:
    basic_salary = st.number_input("Basic Salary (PKR)", min_value=0)
    # -----------------------------
# PRODUCT FILTERING
# -----------------------------

if profession == "Salaried":
    allowed_products = ["Personal Loan", "Auto Loan", "Home Loan", "Solar Loan"]

elif profession == "Staff" or staff_loan:
    allowed_products = ["Personal Loan", "Auto Loan", "Home Loan", "Solar Loan"]

elif profession == "Self-Employed":
    allowed_products = ["Personal Loan", "Auto Loan", "Home Loan", "Solar Loan", "Business Loan"]

else:
    allowed_products = ["Personal Loan", "Auto Loan", "Home Loan", "Solar Loan", "Business Loan"]

# -----------------------------
# PRODUCT SELECTION
# -----------------------------

st.header("Loan Product")

product = st.selectbox("Select Product", allowed_products)

base_rate = PRODUCTS[product]["rate"]
max_tenor_base = PRODUCTS[product]["max_tenor"]
processing_fee = PRODUCTS[product]["fee"]

equity_applicable = PRODUCTS[product]["equity"]

# -----------------------------
# STAFF POLICY OVERRIDES
# -----------------------------

staff_rate = 0.05
staff_tenor_map = {
    "Personal Loan": 7,
    "Auto Loan": 10,
    "Home Loan": 25,
    "Solar Loan": 20
}

if staff_loan:
    rate_used = staff_rate
    max_tenor = staff_tenor_map.get(product, max_tenor_base)
else:
    rate_used = base_rate
    max_tenor = max_tenor_base

# -----------------------------
# TENOR
# -----------------------------

tenor = st.selectbox("Tenor (Years)", list(range(1, max_tenor + 1)))
months = tenor * 12

# -----------------------------
# LOAN MODE SELECTION
# -----------------------------

st.header("Loan Request Mode")

mode = st.radio(
    "Select Mode",
    ["Desired Loan Amount", "Maximum Eligibility"]
)

desired_amount = 0
if mode == "Desired Loan Amount":
    desired_amount = st.number_input("Desired Loan Amount (PKR)", min_value=0)

purpose = st.text_input("Loan Purpose")

# -----------------------------
# ASSET & EQUITY
# -----------------------------

asset_value = 0
equity_pct = 0
equity_amount = 0

if equity_applicable:
    asset_value = st.number_input("Asset Value (PKR)", min_value=0)
    equity_pct = st.slider("Equity %", 20, 50, 20)
    equity_amount = asset_value * equity_pct / 100
    # -----------------------------
# CALCULATION ENGINE
# -----------------------------

if st.button("Run Credit Assessment"):

    if not cnic_valid:
        st.error("Invalid CNIC. Cannot proceed.")
        st.stop()

    dbr_limit = DBR[profession]
    max_emi_allowed = income * dbr_limit

    max_loan_dbr = loan_from_emi(max_emi_allowed, rate_used, months)

    # -----------------------------
    # STAFF CAPS
    # -----------------------------

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

    # -----------------------------
    # FINAL LOAN DECISION INPUT
    # -----------------------------

    if mode == "Desired Loan Amount":
        requested = desired_amount

        approved = min(requested, cap, max_loan_dbr)

        status = "APPROVED" if approved == requested else "PARTIAL / REFERRED"

    else:
        approved = min(cap, max_loan_dbr)
        requested = approved
        status = "AUTO APPROVED (MAX ELIGIBILITY)"

    # -----------------------------
    # EMI CALCULATION
    # -----------------------------

    emi_value = emi(approved, rate_used, months)
    total_repayment = emi_value * months
    markup = total_repayment - approved

    dbr_actual = emi_value / income if income else 0

    eligibility = dbr_actual <= dbr_limit

    # -----------------------------
    # OUTPUT SUMMARY
    # -----------------------------

    st.subheader("Credit Decision Summary")

    st.write("Status:", status)
    st.write("Eligibility:", "Eligible" if eligibility else "Not Eligible")

    st.metric("Requested Amount", f"PKR {requested:,.0f}")
    st.metric("Approved Amount", f"PKR {approved:,.0f}")
    st.metric("Monthly EMI", f"PKR {emi_value:,.0f}")
    st.metric("DBR Utilization", f"{dbr_actual*100:.2f}%")

    st.write("Total Repayment:", f"PKR {total_repayment:,.0f}")
    st.write("Markup:", f"PKR {markup:,.0f}")
    # -----------------------------
# BUSINESS LOAN DETAILS (ONLY IF APPLICABLE)
# -----------------------------

if product == "Business Loan":
    st.subheader("Business Details")

    biz_type = st.selectbox(
        "Nature of Business",
        ["Retail", "Wholesale", "Manufacturing", "Services", "Trading", "Other"]
    )

    biz_years = st.number_input("Years in Business", min_value=0)

    biz_desc = st.text_area(
        "Business Description",
        max_chars=500,
        placeholder="Briefly describe business operations, customers, and purpose of financing"
    )

# -----------------------------
# AMORTIZATION SCHEDULE
# -----------------------------

st.subheader("Amortization Schedule")

df = schedule(approved, rate_used, months, emi_value)
formatted_df = df.copy()

for col in ["EMI", "Principal", "Markup", "Balance"]:
    formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.0f}")

st.dataframe(formatted_df, use_container_width=True)

st.download_button(
    "Download Schedule (CSV)",
    df.to_csv(index=False),
    "schedule.csv",
    "text/csv",
    key="download_schedule"
)

# -----------------------------
# BANK NOTES (ONLY AFTER RESULT)
# -----------------------------

st.subheader("Bank Notes & Disclosures")

st.info(f"DBR Limit: {dbr_limit*100:.0f}%")
st.info(f"Processing Fee: {processing_fee}")

if staff_loan:
    st.info("Staff Pricing: 5% fixed rate applied")

st.info(f"Interest Rate Applied: {rate_used:.2%}")

# -----------------------------
# EQUITY DISPLAY
# -----------------------------

if equity_applicable:
    st.subheader("Equity Details")
    st.write("Equity %:", f"{equity_pct}%")
    st.write("Equity Amount:", f"PKR {equity_amount:,.0f}")

# -----------------------------
# FINAL POLICY SUMMARY (POST-APPROVAL ONLY)
# -----------------------------

st.subheader("Policy Summary")

st.write("Maximum Tenor:", f"{max_tenor} years")
st.write("Product Fee:", processing_fee)
st.write("DBR Limit:", f"{dbr_limit*100:.0f}%")
st.write("Equity Requirement:", "Yes" if equity_applicable else "No")

# -----------------------------
# FINAL NOTE
# -----------------------------

st.caption(
    "Final approval is subject to verification of applicant information and bank credit policy compliance."
)
