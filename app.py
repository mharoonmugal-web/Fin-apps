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

BANKS = [
    "Habib Bank Limited", "United Bank Limited", "Muslim Commercial Bank",
    "Allied Bank Limited", "Bank Alfalah", "Meezan Bank",
    "Bank Al Habib", "Faysal Bank", "The Bank of Punjab",
    "Askari Bank", "JS Bank", "Soneri Bank"
]

# -----------------------------
# CREDIT POLICY ENGINE
# -----------------------------

def get_policy(product, staff):
    base = PRODUCTS[product]

    policy = {
        "rate": base["rate"],
        "max_tenor": base["max_tenor"],
        "equity_required": True
    }

    if staff:
        policy["rate"] = 0.05

        if product == "Personal Loan":
            policy["max_tenor"] = 7

        if product in ["Auto Loan", "Home Loan", "Solar Loan"]:
            policy["equity_required"] = False

    return policy

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

    return pd.DataFrame(data, columns=["Month", "EMI", "Principal", "Markup", "Balance"])

# -----------------------------
# UI
# -----------------------------

st.title("Digital Credit Engine")

st.header("Applicant Information")

c1, c2, c3 = st.columns(3)

name = c1.text_input("Full Name")

# -----------------------------
# CNIC AUTO FORMAT (FIXED)
# -----------------------------

cnic_input = c2.text_input("CNIC (13 digits)")

cnic_digits = re.sub(r"\D", "", cnic_input)[:13]

formatted_cnic = ""

if cnic_digits:
    if len(cnic_digits) <= 5:
        formatted_cnic = cnic_digits
    elif len(cnic_digits) <= 12:
        formatted_cnic = cnic_digits[:5] + "-" + cnic_digits[5:]
    else:
        formatted_cnic = cnic_digits[:5] + "-" + cnic_digits[5:12] + "-" + cnic_digits[12:]

    c2.text_input("Formatted CNIC", value=formatted_cnic, disabled=True)

if cnic_input and len(cnic_digits) != 13:
    c2.error("CNIC must be 13 digits")

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
service_years = 0
service_months = 0

if staff_loan:
    basic_salary = st.number_input("Basic Salary (PKR)", min_value=0)

# -----------------------------
# PRODUCT
# -----------------------------

st.header("Loan Product")

product = st.selectbox("Select Product", list(PRODUCTS.keys()))

policy = get_policy(product, staff_loan)

rate_used = policy["rate"]
max_tenor = policy["max_tenor"]
equity_required = policy["equity_required"]

# -----------------------------
# HOME LOAN STAFF TENOR RULE
# -----------------------------

if staff_loan and product == "Home Loan":

    st.subheader("Remaining Service Details")

    service_years = st.number_input("Remaining Service (Years)", min_value=0, step=1)
    service_months = st.number_input("Remaining Service (Months)", min_value=0, max_value=11)

    total_service_months = service_years * 12 + service_months
    service_cap_years = total_service_months // 12

    max_tenor = min(max_tenor, 25, service_cap_years)

# -----------------------------
# TENOR
# -----------------------------

tenor = st.selectbox("Tenor (Years)", list(range(1, max_tenor + 1)))
months = tenor * 12

# -----------------------------
# PURPOSE
# -----------------------------

if product == "Personal Loan":
    purpose = st.selectbox("Purpose", ["Domestic", "Travel", "Marriage", "Education", "Other"])
    if purpose == "Other":
        purpose = st.text_input("Specify Purpose")
else:
    purpose = st.text_input("Purpose")

# -----------------------------
# ASSET
# -----------------------------

asset = 0
equity_pct = 0
equity_amount = 0

if product in ["Auto Loan", "Home Loan", "Solar Loan"]:
    st.header("Asset Details")
    asset = st.number_input("Asset Value (PKR)", min_value=0)

# -----------------------------
# CALCULATION
# -----------------------------

if st.button("Calculate Eligibility"):

    dbr_limit = DBR[profession]
    max_emi = income * dbr_limit

    max_loan_dbr = loan_from_emi(max_emi, rate_used, months)

    # -------------------------
    # STAFF CAPS
    # -------------------------

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

    # -------------------------
    # EQUITY LOGIC
    # -------------------------

    if product in ["Auto Loan", "Home Loan", "Solar Loan"] and equity_required:

        if product == "Auto Loan":
            equity_pct = 30
        else:
            equity_pct = 20

        equity_amount = asset * equity_pct / 100
        asset_loan = asset * (1 - equity_pct / 100)

    else:
        asset_loan = cap
        equity_amount = 0

    approved = min(max_loan_dbr, asset_loan, cap)

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
    # EQUITY DISPLAY
    # -----------------------------

    if product in ["Auto Loan", "Home Loan", "Solar Loan"] and equity_required:
        st.subheader("Equity Details")
        st.write("Equity %:", f"{equity_pct}%")
        st.write("Equity Amount:", f"PKR {equity_amount:,.0f}")

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
    # ENDNOTES
    # -----------------------------

    st.subheader("Bank Notes")

    if staff_loan:
        st.info("Staff Pricing: 5% fixed rate applied")
    else:
        if product == "Personal Loan":
            st.info("Rate: 35% amortized")
        elif product == "Auto Loan":
            st.info("Rate: KIBOR + 5%")
        elif product == "Home Loan":
            st.info("Rate: KIBOR + 3%")
        elif product == "Solar Loan":
            st.info("Rate: KIBOR + 5%")
        elif product == "Business Loan":
            st.info("Rate: 35% amortized")
