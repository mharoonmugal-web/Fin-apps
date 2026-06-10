import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Finance Calculator",
    layout="wide"
)

st.title("Personal Finance Loan Calculator")

DBR_LIMIT = 0.40

mode = st.radio(
    "Select Mode",
    ["Maximum Eligible Loan", "Affordability Check"]
)

income = st.number_input(
    "Monthly Take Home Income (PKR)",
    min_value=1.0,
    value=100000.0
)

apr = st.number_input(
    "APR (%)",
    min_value=0.0,
    value=10.0
)

years = st.selectbox(
    "Tenor",
    [1, 2, 3, 4, 5]
)

months = years * 12


def calculate_emi(principal, annual_rate, months):
    monthly_rate = annual_rate / 12 / 100

    if monthly_rate == 0:
        return principal / months

    emi = (
        principal
        * monthly_rate
        * ((1 + monthly_rate) ** months)
        / (((1 + monthly_rate) ** months) - 1)
    )

    return emi


def calculate_loan_from_emi(emi, annual_rate, months):
    monthly_rate = annual_rate / 12 / 100

    if monthly_rate == 0:
        return emi * months

    principal = (
        emi
        * (
            ((1 + monthly_rate) ** months) - 1
        )
        / (
            monthly_rate
            * ((1 + monthly_rate) ** months)
        )
    )

    return principal


if mode == "Affordability Check":
    desired_loan = st.number_input(
        "Desired Loan Amount (PKR)",
        min_value=1.0,
        value=500000.0
    )

if st.button("Calculate"):

    if mode == "Maximum Eligible Loan":

        max_emi = income * DBR_LIMIT

        loan_amount = calculate_loan_from_emi(
            max_emi,
            apr,
            months
        )

        emi = max_emi

    else:

        loan_amount = desired_loan

        emi = calculate_emi(
            loan_amount,
            apr,
            months
        )

    total_repayment = emi * months
    total_markup = total_repayment - loan_amount
    dbr = (emi / income) * 100

    status = (
        "Eligible"
        if dbr <= 40
        else "Not Eligible"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Loan Amount",
        f"PKR {loan_amount:,.0f}"
    )

    col2.metric(
        "Monthly Installment",
        f"PKR {emi:,.0f}"
    )

    col3.metric(
        "DBR",
        f"{dbr:.2f}%"
    )

    st.subheader("Summary")

    st.write(
        f"**Total Repayment:** PKR {total_repayment:,.0f}"
    )

    st.write(
        f"**Total Markup:** PKR {total_markup:,.0f}"
    )

    st.write(
        f"**Eligibility Status:** {status}"
    )

    balance = loan_amount

    schedule = []

    monthly_rate = apr / 12 / 100

    for month in range(1, months + 1):

        interest = balance * monthly_rate

        principal_component = emi - interest

        balance -= principal_component

        if balance < 0:
            balance = 0

        schedule.append([
            month,
            round(emi, 2),
            round(principal_component, 2),
            round(interest, 2),
            round(balance, 2)
        ])

    df = pd.DataFrame(
        schedule,
        columns=[
            "Month",
            "EMI",
            "Principal",
            "Markup",
            "Outstanding Balance"
        ]
    )

    st.subheader("Amortization Schedule")

    st.dataframe(
        df,
        use_container_width=True
    )

    csv = df.to_csv(index=False)

    st.download_button(
        label="Download Schedule (CSV)",
        data=csv,
        file_name="amortization_schedule.csv",
        mime="text/csv"
    )
