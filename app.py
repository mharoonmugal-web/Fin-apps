import streamlit as st
import pandas as pd

st.set_page_config(page_title="Alpha Finance - Eligibility Engine", layout="wide")

# -----------------------------
# CONFIG
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
# UI
# -----------------------------

st.title("Digital Credit Engine")

st.header("Applicant Details")

col1, col2, col3 = st.columns(3)

name = col1.text_input("Name")
cnic = col2.text_input("CNIC")
gender = col3.selectbox("Gender", ["Male", "Female"])

col4, col5 = st.columns(2)

profession = col4.selectbox("Profession", ["Salaried", "Self-Employed", "Businessman"])
income = col5.number_input("Monthly Income (PKR)", min_value=0)

st.header("Product Selection")

product = st.selectbox("Loan Product", list(PRODUCTS.keys()))

rate = PRODUCTS[product]["rate"]
tenor_years = PRODUCTS[product]["tenor"]

tenor = st.selectbox("Tenor (Years)", list(range(1, tenor_years + 1)))
months = tenor * 12

# -----------------------------
# ASSET LOGIC
# -----------------------------

asset_value = 0
equity_pct = 0

if product != "Personal Loan":
    st.subheader("Asset Details")

    asset_value = st.number_input("Asset Value (PKR)", min_value=0)

    if product == "Auto Loan":
        equity_pct = st.slider("Equity %", 30, 50, 30)
    elif product == "Solar Loan":
        equity_pct = st.slider("Equity %", 20, 50, 20)
    elif product == "Home Loan":
        equity_pct = st.slider("Equity %", 20, 50, 20)

# -----------------------------
# CALCULATION
# -----------------------------

if st.button("Calculate"):

    dbr_limit = DBR_RULE[profession]
    max_emi_allowed = income * dbr_limit

    # -------------------------
    # DBR BASED LOAN (HARD CAP)
    # -------------------------
    max_loan_by_dbr = loan_from_emi(max_emi_allowed, rate, months)

    # -------------------------
    # ASSET BASED LOAN
    # -------------------------
    if product == "Personal Loan":
        asset_based_loan = max_loan_by_dbr
    else:
        asset_based_loan = asset_value * (1 - equity_pct / 100)
# -----------------------------
# DYNAMIC ENDNOTES ENGINE
# -----------------------------

st.subheader("Banking Notes & Disclosures")

notes = []

# DBR note
notes.append(f"Maximum DBR applicable for this profile: {dbr_limit*100:.0f}%")

# KIBOR note
notes.append("Reference KIBOR: 12.96% (subject to change)")

# Product-specific markup note
if product == "Personal Loan":
    notes.append("Pricing: Fixed 35% p.a. amortized")
elif product == "Auto Loan":
    notes.append("Pricing: KIBOR + 5% (floating)")
    notes.append("Insurance applies with reducing asset coverage structure")
elif product == "Home Loan":
    notes.append("Pricing: KIBOR + 3% (floating)")
elif product == "Solar Loan":
    notes.append("Pricing: KIBOR + 5% (floating)")
elif product == "Business Loan":
    notes.append("Pricing: KIBOR + 5% (floating)")

# Asset notes
if product != "Personal Loan":
    notes.append(f"Equity requirement applied: {equity_pct}%")
    notes.append("Final approval based on lower of DBR capacity vs asset financing")

# Display
for n in notes:
    st.info("• " + n)
    # -------------------------
    # FINAL APPROVED LOAN
    # -------------------------
    approved_loan = min(max_loan_by_dbr, asset_based_loan)

    emi_value = emi(approved_loan, rate, months)

    total_payment = emi_value * months
    markup = total_payment - approved_loan
    dbr_actual = emi_value / income

    eligible = dbr_actual <= dbr_limit

    # -------------------------
    # OUTPUT
    # -------------------------

    st.subheader("Credit Assessment Result")

    st.success(
        f"Max loan bank can offer as per your DBR is: PKR {max_loan_by_dbr:,.0f}"
    )

    colA, colB, colC = st.columns(3)

    colA.metric("Approved Loan", f"PKR {approved_loan:,.0f}")
    colB.metric("Monthly EMI", f"PKR {emi_value:,.0f}")
    colC.metric("DBR", f"{dbr_actual*100:.2f}%")

    st.write("Status:", "Eligible" if eligible else "Not Eligible")

    st.subheader("Financial Summary")
    st.write("Total Repayment:", f"PKR {total_payment:,.0f}")
    st.write("Total Markup:", f"PKR {markup:,.0f}")

    # -------------------------
    # AMORTIZATION
    # -------------------------

    st.subheader("Amortization Schedule")

    df = schedule(approved_loan, rate, months, emi_value)
    st.dataframe(df, use_container_width=True)

    st.download_button(
    "Download Schedule (CSV)",
    df.to_csv(index=False),
    "schedule.csv",
    "text/csv",
    key="download_schedule_main"
)
