import streamlit as st
import pandas as pd
import re

# -----------------------------

# PAGE CONFIG

# -----------------------------

st.set_page_config(
page_title="Digital Credit Engine",
layout="wide"
)

# -----------------------------

# CONFIGURATION

# -----------------------------

KIBOR = 12.96 / 100

PRODUCTS = {
"Personal Loan": {
"rate": 0.35,
"max_tenor": 5,
"processing_fee": "PKR 2,500"
},
"Auto Loan": {
"rate": KIBOR + 0.05,
"max_tenor": 5,
"processing_fee": "PKR 8,000"
},
"Home Loan": {
"rate": KIBOR + 0.03,
"max_tenor": 20,
"processing_fee": "PKR 12,000"
},
"Solar Loan": {
"rate": KIBOR + 0.05,
"max_tenor": 8,
"processing_fee": "PKR 5,000"
},
"Business Loan": {
"rate": KIBOR + 0.05,
"max_tenor": 5,
"processing_fee": "TBA"
}
}

DBR_RULES = {
"Salaried": 0.40,
"Self-Employed": 0.50,
"Businessman": 0.50
}

BANKS = [
"HBL",
"UBL",
"MCB",
"ABL",
"Bank Alfalah",
"Meezan Bank",
"Bank Al Habib",
"Faysal Bank",
"Askari Bank",
"BankIslami",
"JS Bank",
"Soneri Bank"
]

# -----------------------------

# FUNCTIONS

# -----------------------------

def calculate_emi(principal, annual_rate, months):

```
monthly_rate = annual_rate / 12

if monthly_rate == 0:
    return principal / months

return (
    principal
    * monthly_rate
    * (1 + monthly_rate) ** months
    / ((1 + monthly_rate) ** months - 1)
)
```

def calculate_loan_from_emi(emi_value, annual_rate, months):

```
monthly_rate = annual_rate / 12

return (
    emi_value
    * ((1 + monthly_rate) ** months - 1)
    / (monthly_rate * (1 + monthly_rate) ** months)
)
```

def build_amortization_schedule(
principal,
annual_rate,
months,
emi_value
):

```
monthly_rate = annual_rate / 12

balance = principal

rows = []

for month in range(1, months + 1):

    markup = balance * monthly_rate

    principal_component = emi_value - markup

    balance -= principal_component

    rows.append([
        month,
        round(emi_value, 2),
        round(principal_component, 2),
        round(markup, 2),
        round(max(balance, 0), 2)
    ])

return pd.DataFrame(
    rows,
    columns=[
        "Month",
        "EMI",
        "Principal",
        "Markup",
        "Outstanding Balance"
    ]
)
```

# -----------------------------

# HEADER

# -----------------------------

st.title("Digital Credit Engine")

st.caption(
"Banking-style financing eligibility assessment tool"
)

# -----------------------------

# APPLICANT INFORMATION

# -----------------------------

st.header("Applicant Information")

col1, col2, col3 = st.columns(3)

name = col1.text_input("Full Name")

cnic = col2.text_input(
"CNIC (xxxxx-xxxxxxx-x)",
max_chars=15
)

if cnic and not re.fullmatch(r"\d{5}-\d{7}-\d", cnic):
col2.error(
"Format must be 12345-1234567-1"
)

gender = col3.selectbox(
"Gender",
["Male", "Female"]
)

col4, col5, col6 = st.columns(3)

profession = col4.selectbox(
"Profession",
[
"Salaried",
"Self-Employed",
"Businessman"
]
)

income = col5.number_input(
"Monthly Income (PKR)",
min_value=0.0,
step=1000.0
)

experience = col6.number_input(
"Experience (Years)",
min_value=0,
step=1
)

# -----------------------------

# BANKING RELATIONSHIP

# -----------------------------

st.header("Banking Relationship")

col7, col8 = st.columns(2)

bank = col7.selectbox(
"Account Maintaining Bank",
BANKS
)

bank_years = col8.number_input(
"Relationship Duration (Years)",
min_value=0,
step=1
)

# -----------------------------

# PRODUCT DETAILS

# -----------------------------

st.header("Financing Requirement")

product = st.selectbox(
"Loan Product",
list(PRODUCTS.keys())
)

annual_rate = PRODUCTS[product]["rate"]

max_tenor = PRODUCTS[product]["max_tenor"]

tenor_years = st.selectbox(
"Tenor (Years)",
list(range(1, max_tenor + 1))
)

months = tenor_years * 12

# -----------------------------

# PURPOSE

# -----------------------------

if product == "Personal Loan":

```
purpose = st.selectbox(
    "Purpose",
    [
        "Domestic Needs",
        "Travelling",
        "Marriage",
        "Education",
        "Entertainment",
        "Other"
    ]
)

if purpose == "Other":
    purpose = st.text_input(
        "Specify Purpose"
    )
```

else:

```
purpose = st.text_input(
    "Specify Purpose"
)
```

# -----------------------------

# ASSET BASED PRODUCTS

# -----------------------------

asset_value = 0
equity_pct = 0

if product in [
"Auto Loan",
"Home Loan",
"Solar Loan"
]:

```
st.header("Asset Details")

asset_value = st.number_input(
    "Asset Value (PKR)",
    min_value=0.0,
    step=10000.0
)

if product == "Auto Loan":
    equity_pct = st.slider(
        "Equity %",
        30,
        50,
        30
    )

elif product == "Home Loan":
    equity_pct = st.slider(
        "Equity %",
        20,
        50,
        20
    )

elif product == "Solar Loan":
    equity_pct = st.slider(
        "Equity %",
        20,
        50,
        20
    )
```

# -----------------------------

# CALCULATE BUTTON

# -----------------------------

calculate = st.button(
"Calculate Eligibility"
)
# -----------------------------

# CALCULATION ENGINE

# -----------------------------

if calculate:

```
dbr_limit = DBR_RULES[profession]

max_emi_allowed = income * dbr_limit

max_loan_by_dbr = calculate_loan_from_emi(
    max_emi_allowed,
    annual_rate,
    months
)

# -----------------------------
# ASSET / DBR RECONCILIATION
# -----------------------------

if product in [
    "Auto Loan",
    "Home Loan",
    "Solar Loan"
]:

    required_financing = (
        asset_value *
        (1 - equity_pct / 100)
    )

    approved_loan = min(
        max_loan_by_dbr,
        required_financing
    )

    equity_amount = (
        asset_value *
        equity_pct / 100
    )

    shortfall = max(
        0,
        required_financing - approved_loan
    )

else:

    required_financing = max_loan_by_dbr

    approved_loan = max_loan_by_dbr

    equity_amount = 0

    shortfall = 0

# -----------------------------
# EMI CALCULATION
# -----------------------------

emi_value = calculate_emi(
    approved_loan,
    annual_rate,
    months
)

total_repayment = (
    emi_value * months
)

total_markup = (
    total_repayment -
    approved_loan
)

actual_dbr = (
    emi_value / income
    if income > 0
    else 0
)

# -----------------------------
# RESULTS
# -----------------------------

st.header(
    "Credit Assessment Result"
)

st.success(
    f"Max loan bank can offer as per your DBR is: "
    f"PKR {max_loan_by_dbr:,.0f}"
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Approved Loan",
    f"PKR {approved_loan:,.0f}"
)

col2.metric(
    "Monthly EMI",
    f"PKR {emi_value:,.0f}"
)

col3.metric(
    "Actual DBR",
    f"{actual_dbr*100:.2f}%"
)

# -----------------------------
# ASSET DETAILS
# -----------------------------

if product in [
    "Auto Loan",
    "Home Loan",
    "Solar Loan"
]:

    st.subheader(
        "Asset Financing Summary"
    )

    st.write(
        f"Asset Value: PKR {asset_value:,.0f}"
    )

    st.write(
        f"Equity Contribution ({equity_pct}%): "
        f"PKR {equity_amount:,.0f}"
    )

    st.write(
        f"Required Financing: "
        f"PKR {required_financing:,.0f}"
    )

    st.write(
        f"Financing Shortfall: "
        f"PKR {shortfall:,.0f}"
    )

# -----------------------------
# FINANCIAL SUMMARY
# -----------------------------

st.subheader(
    "Financial Summary"
)

st.write(
    f"Total Repayment: "
    f"PKR {total_repayment:,.0f}"
)

st.write(
    f"Total Markup: "
    f"PKR {total_markup:,.0f}"
)

# -----------------------------
# AMORTIZATION
# -----------------------------

st.subheader(
    "Amortization Schedule"
)

amort_df = build_amortization_schedule(
    approved_loan,
    annual_rate,
    months,
    emi_value
)

st.dataframe(
    amort_df,
    use_container_width=True
)

# -----------------------------
# DOWNLOAD
# -----------------------------

st.download_button(
    label="Download Schedule (CSV)",
    data=amort_df.to_csv(index=False),
    file_name="amortization_schedule.csv",
    mime="text/csv",
    key="amortization_download"
)

# -----------------------------
# DYNAMIC ENDNOTES
# -----------------------------

st.header(
    "Banking Notes & Disclosures"
)

notes = []

notes.append(
    f"Maximum DBR applicable: "
    f"{dbr_limit*100:.0f}%"
)

if product == "Personal Loan":

    notes.append(
        "Pricing: Fixed 35.00% p.a. "
        "(amortized)"
    )

    notes.append(
        "Processing Fee: PKR 2,500"
    )

elif product == "Auto Loan":

    notes.append(
        "Pricing: KIBOR (12.96%) + "
        "5.00% = 17.96% p.a."
    )

    notes.append(
        "Processing Fee: PKR 8,000"
    )

    notes.append(
        "Insurance applicable as per "
        "bank policy"
    )

elif product == "Home Loan":

    notes.append(
        "Pricing: KIBOR (12.96%) + "
        "3.00% = 15.96% p.a."
    )

    notes.append(
        "Processing Fee: PKR 12,000"
    )

elif product == "Solar Loan":

    notes.append(
        "Pricing: KIBOR (12.96%) + "
        "5.00% = 17.96% p.a."
    )

    notes.append(
        "Processing Fee: PKR 5,000"
    )

elif product == "Business Loan":

    notes.append(
        "Pricing: KIBOR (12.96%) + "
        "5.00% = 17.96% p.a."
    )

    notes.append(
        "Processing Fee: TBA"
    )

if product in [
    "Auto Loan",
    "Home Loan",
    "Solar Loan"
]:

    notes.append(
        f"Equity requirement applied: "
        f"{equity_pct}%"
    )

    notes.append(
        "Final financing approval is "
        "based on lower of DBR capacity "
        "and financing requirement."
    )

for note in notes:
    st.info(note)
```
