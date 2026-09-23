import streamlit as st
import pandas as pd
from calculations.loans import months_to_repay, amortisation_schedule, calculate_monthly_payment
from calculations.loan_prediction import predict_max_loan, plan_goal_with_loan
from calculations.goals import calculate_goal_gap
from calculations.goals_ai import explain_goal_with_loan
from calculations.language import show_language_picker, t

st.set_page_config(
    page_title="Loans",
    page_icon="💳",
    layout="wide"
)

show_language_picker()

st.title(t("💳 Loans"))

tab1, tab2 = st.tabs([t("I already have a loan"), t("How much can I borrow?")])

with tab1:
    loans = st.session_state.get("loans", [])

    if not loans:
        st.info(t("You haven't added any loans yet — add one on your Finances page."))
    else:
        st.subheader(t("When will I repay my existing loan?"))

        loan_names = [l["name"] for l in loans]
        selected_name = st.selectbox(t("Which loan?"), loan_names)
        selected_loan = next(l for l in loans if l["name"] == selected_name)

        principal = selected_loan["principal"]
        annual_rate = selected_loan.get("rate", 9.0)
        monthly_payment = selected_loan["payment"]

        st.write(
            f"{t('Owing')} Rs {principal:,.0f} {t('at')} {annual_rate}%, "
            f"{t('paying')} Rs {monthly_payment:,.0f}{t('/month')}"
        )

        if principal <= 0:
            st.error(t("Loan amount must be greater than 0."))
        elif monthly_payment <= 0:
            st.error(t("Monthly payment must be greater than 0."))
        elif monthly_payment > principal:
            st.info(f"ℹ️ {t('Since your payment is more than what you owe, you would pay this off in 1 month.')}")
        else:
            months = months_to_repay(principal, annual_rate, monthly_payment)

            if months is None:
                st.error(t("⚠️ Your payment doesn't cover the interest — at this rate, you'll never pay off this loan."))
            else:
                years = months / 12
                st.success(f"✅ {t('You will repay your loan in')} **{months} {t('months')}** (~{years:.1f} {t('years')})")

                schedule = amortisation_schedule(principal, annual_rate, monthly_payment, months)

                interest_data = [m["interest_portion"] for m in schedule]
                principal_data = [m["principal_portion"] for m in schedule]

                st.subheader(t("📊 Interest vs. Principal Over Time"))

                chart_df = pd.DataFrame({
                    t("Interest paid (Rs)"): interest_data,
                    t("Principal paid (Rs)"): principal_data
                }, index=[f"{t('Month')} {m}" for m in range(1, len(interest_data) + 1)])

                st.line_chart(chart_df)
                st.caption(f"{t('Showing the full')} {len(interest_data)}-{t('month repayment period, from month 1 to month')} {len(interest_data)}.")

        # keep the existing-loan-payment shared value in sync for Tab 2's prefill,
        # using the SELECTED loan's payment (not a manual re-entry)
        st.session_state["existing_loan_payment"] = monthly_payment
        st.session_state["loan2_debt"] = monthly_payment


with tab2:
    st.subheader(t("How much can I realistically borrow?"))

    income = st.session_state.get("income", 0.0)
    expenses = st.session_state.get("expenses", 0.0)

    st.write(f"{t('Using your profile: income')} Rs {income}, {t('expenses')} Rs {expenses}")

    age = st.number_input(t("Your age"), min_value=18, max_value=100, step=1, key="loan2_age")

    existing_debt = st.number_input(
        t("Any existing debt payments? (Rs/month)"),
        min_value=0.0, step=100.0,
        value=st.session_state.get("existing_loan_payment", 0.0),
        key="loan2_debt"
    )
    credit_score = st.slider(t("Estimated credit score"), 300, 850, 680, key="loan2_credit")

    if st.button(t("Predict my borrowing power"), type="primary"):
        if income <= 0:
            st.error(t("Please fill in your income on the Your Finances page first."))
        else:
            predicted = predict_max_loan(income, expenses, existing_debt, credit_score, age)
            st.success(f"📊 {t('Based on your profile, you could realistically borrow up to')} **Rs {predicted:,.2f}**")

            goals = st.session_state.get("goals", [])
            savings_rate = st.session_state.get("savings_rate", 0.0)
            current_savings = st.session_state.get("current_savings", 0.0)
            monthly_savings = st.session_state.get("monthly_savings", 0.0)

            if goals:
                st.subheader(t("🎯 How this could help your goals"))

                for goal in goals:
                    deadline_months = goal["years"] * 12

                    gap_info = calculate_goal_gap(
                        current_savings, monthly_savings, savings_rate,
                        deadline_months, goal["amount"]
                    )

                    if gap_info["gap"] <= 0:
                        st.success(f"✅ {t('You are on track to fully save for')} **{goal['name']}** {t('without needing a loan.')}")
                        continue

                    loan_plan = plan_goal_with_loan(gap_info["gap"], predicted)

                    with st.spinner(f"{t('Thinking about')} {goal['name']}..."):
                        explanation = explain_goal_with_loan(goal, gap_info, loan_plan, predicted)

                    st.info(f"**{goal['name']}**: {explanation}")