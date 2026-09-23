import streamlit as st
import pandas as pd
from calculations.loans import months_to_repay, amortisation_schedule, calculate_monthly_payment
from calculations.loan_prediction import predict_max_loan, plan_goal_with_loan
from calculations.goals import calculate_goal_gap
from calculations.goals_ai import explain_goal_with_loan, explain_loan_payoff_plan
from calculations.language import show_language_picker, t

st.set_page_config(
    page_title="Loans",
    page_icon="\U0001f4b3",
    layout="wide"
)

show_language_picker()

st.title(t("\U0001f4b3 Loans"))

tab1, tab2 = st.tabs([t("I already have a loan"), t("How much can I borrow?")])

with tab1:
    loans = st.session_state.get("loans", [])

    if not loans:
        st.info(t("You haven't added any loans yet — add one on your Finances page."))
    else:
        st.subheader(t("Plan how you'll pay off your loan"))

        loan_names = [l["name"] for l in loans]
        selected_name = st.selectbox(t("Which loan?"), loan_names)
        selected_loan = next(l for l in loans if l["name"] == selected_name)

        principal = selected_loan["principal"]
        annual_rate = selected_loan.get("rate", 9.0)
        current_payment = selected_loan["payment"]

        st.write(
            f"{t('Owing')} Rs {principal:,.0f} {t('at')} {annual_rate}%, "
            f"{t('currently paying')} Rs {current_payment:,.0f}{t('/month')}"
        )

        desired_years = st.number_input(
            t("By when do you want to pay this off? (years)"),
            min_value=1, max_value=30, step=1, value=5,
            key="loan_payoff_years"
        )

        if principal <= 0:
            st.error(t("Loan amount must be greater than 0."))
        else:
            # the REQUIRED payment to hit the user's own chosen timeframe
            required_payment = calculate_monthly_payment(principal, annual_rate, desired_years)

            st.info(
                f"\U0001f4a1 {t('To pay this off in')} {desired_years} {t('years, you would need to pay')} "
                f"**Rs {required_payment:,.2f}{t('/month')}**."
            )

            if current_payment <= 0:
                st.warning(t("Enter your current monthly payment on your Finances page to compare."))
            elif current_payment >= required_payment:
                # they're already paying enough (or more) -- show their ACTUAL payoff time
                actual_months = months_to_repay(principal, annual_rate, current_payment)
                if actual_months:
                    actual_years = actual_months / 12
                    st.success(
                        f"\u2705 {t('At your current payment of')} Rs {current_payment:,.0f}{t('/month')}, "
                        f"{t('you will actually pay this off in')} **{actual_months} {t('months')}** "
                        f"(~{actual_years:.1f} {t('years')}) — {t('at or ahead of your')} {desired_years}-{t('year goal')}!"
                    )
            else:
                gap = required_payment - current_payment
                st.warning(
                    f"\u26a0\ufe0f {t('You are currently paying')} Rs {current_payment:,.0f}{t('/month')}, "
                    f"{t('but you would need Rs')} {required_payment:,.2f}{t('/month to hit your')} "
                    f"{desired_years}-{t('year goal')} — {t('a gap of Rs')} {gap:,.2f}{t('/month')}."
                )

                if st.button(t("\U0001f4a1 How can I close this gap?"), key="loan_gap_ai"):
                    with st.spinner(t("Thinking...")):
                        expense_categories = st.session_state.get("expense_categories", [])
                        explanation = explain_loan_payoff_plan(
                            selected_name, principal, annual_rate, desired_years,
                            required_payment, current_payment, expense_categories
                        )
                    st.info(explanation)

            # chart -- always show based on the payment they're ACTUALLY making
            if current_payment > 0:
                months_for_chart = months_to_repay(principal, annual_rate, current_payment)
                if months_for_chart:
                    schedule = amortisation_schedule(principal, annual_rate, current_payment, months_for_chart)

                    interest_data = [m["interest_portion"] for m in schedule]
                    principal_data = [m["principal_portion"] for m in schedule]

                    st.subheader(t("\U0001f4ca Interest vs. Principal Over Time"))

                    chart_df = pd.DataFrame({
                        t("Interest paid (Rs)"): interest_data,
                        t("Principal paid (Rs)"): principal_data
                    }, index=[f"{t('Month')} {m}" for m in range(1, len(interest_data) + 1)])

                    st.line_chart(chart_df)
                    st.caption(f"{t('Showing the full')} {len(interest_data)}-{t('month repayment period, from month 1 to month')} {len(interest_data)}.")
                else:
                    st.error(t("⚠️ Your current payment doesn't cover the interest — at this rate, you'll never pay off this loan."))

        st.session_state["existing_loan_payment"] = current_payment
        st.session_state["loan2_debt"] = current_payment

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
            st.success(f"\U0001f4ca {t('Based on your profile, you could realistically borrow up to')} **Rs {predicted:,.2f}**")

            goals = st.session_state.get("goals", [])
            savings_rate = st.session_state.get("savings_rate", 0.0)
            current_savings = st.session_state.get("current_savings", 0.0)
            monthly_savings = st.session_state.get("monthly_savings", 0.0)

            if goals:
                st.subheader(t("\U0001f3af How this could help your goals"))

                for goal in goals:
                    deadline_months = goal["years"] * 12

                    gap_info = calculate_goal_gap(
                        current_savings, monthly_savings, savings_rate,
                        deadline_months, goal["amount"]
                    )

                    if gap_info["gap"] <= 0:
                        st.success(f"\u2705 {t('You are on track to fully save for')} **{goal['name']}** {t('without needing a loan.')}")
                        continue

                    loan_plan = plan_goal_with_loan(gap_info["gap"], predicted)

                    with st.spinner(f"{t('Thinking about')} {goal['name']}..."):
                        explanation = explain_goal_with_loan(goal, gap_info, loan_plan, predicted)

                    st.info(f"**{goal['name']}**: {explanation}")