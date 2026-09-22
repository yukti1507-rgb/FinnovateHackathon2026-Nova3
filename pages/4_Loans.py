import streamlit as st
from calculations.loans import months_to_repay, amortisation_schedule, calculate_monthly_payment

st.set_page_config(page_title="Loans", page_icon="💳", layout="wide")
st.title("💳 Loans")



has_loan = st.radio("Are you currently repaying a loan? ", ["Yes", "No"], horizontal=True) == "Yes"

if has_loan:
    st.subheader("When will I repay my existing loan?")

    principal = st.number_input("How much do you still owe? (Rs)", min_value=0.0, step=500.0)
    annual_rate = st.slider("Interest rate (%)", 0.0, 20.0, 9.0, step=0.1)

    if principal > 0:
        suggested_payment = calculate_monthly_payment(principal, annual_rate, term_years=5)
        st.caption(f"💡 For reference, paying this off over 5 years would be about Rs {suggested_payment}/month")

    monthly_payment = st.number_input("How much do you pay per month? (Rs)", min_value=0.0, step=100.0)

    if st.button("Calculate repayment time", type="primary"):
        if principal <= 0:
            st.error("Loan amount must be greater than 0.")
        elif monthly_payment <= 0:
            st.error("Monthly payment must be greater than 0.")
        elif monthly_payment > principal:
            st.info(f"ℹ️ Since your payment (Rs {monthly_payment}) is more than what you owe, you'd pay this off in 1 month.")
        else:
            months = months_to_repay(principal, annual_rate, monthly_payment)

            if months is None:
                st.error("⚠️ Your payment doesn't cover the interest — at this rate, you'll never pay off this loan.")
            else:
                years = months / 12
                st.success(f"✅ You'll repay your loan in **{months} months** (~{years:.1f} years)")

                schedule = amortisation_schedule(principal, annual_rate, monthly_payment, months)

                interest_data = [m["interest_portion"] for m in schedule]
                principal_data = [m["principal_portion"] for m in schedule]

                st.subheader("📊 Interest vs. Principal Over Time")
                st.line_chart({
                    "Interest paid": interest_data,
                    "Principal paid": principal_data
                })

else:
    st.info("You currently are not repaying a loan.")