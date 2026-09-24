# pages/loans.py - "Loans": your loans, a payoff planner, and borrowing power in one page

import math
import streamlit as st
import plotly.graph_objects as go
import calculations.loans 

try:
    from calculations.loans import months_to_repay, amortisation_schedule, calculate_monthly_payment
except ImportError:
    # calculations/loans.py is missing these functions -> use built-in versions so this page still works
    def calculate_monthly_payment(principal, annual_rate, years):
        n = int(years * 12)
        r = annual_rate / 100 / 12
        if r == 0:
            return principal / n
        return principal * r / (1 - (1 + r) ** -n)

    def months_to_repay(principal, annual_rate, payment):
        r = annual_rate / 100 / 12
        if payment <= principal * r:
            return None
        if r == 0:
            return math.ceil(principal / payment)
        return math.ceil(-math.log(1 - principal * r / payment) / math.log(1 + r))

    def amortisation_schedule(principal, annual_rate, payment, months):
        r = annual_rate / 100 / 12
        balance, rows = principal, []
        for m in range(1, int(months) + 1):
            interest = balance * r
            princ = min(payment - interest, balance)
            balance -= princ
            rows.append({"month": m, "interest_portion": interest,
                         "principal_portion": princ, "balance": max(balance, 0)})
            if balance <= 0.005:
                break
        return rows
from calculations.loan_prediction import predict_max_loan, plan_goal_with_loan
from calculations.goals import calculate_goal_gap
from calculations.goals_ai import explain_goal_with_loan, explain_loan_payoff_plan
from calculations.language import show_language_picker, t

st.set_page_config(
    page_title="Loans",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from ui import (apply_theme, navbar, require_login, page_header, style_fig,
                stat_card, badge, money)

apply_theme()
require_login()
navbar(active="Loans")

show_language_picker()

page_header(t("Loans"), t("Everything you owe, how to pay it off, and what you could borrow."))
st.write("")

ss = st.session_state
if "loans" not in ss:
    ss["loans"] = []
loans = ss["loans"]

income = ss.get("income", 0.0) or 0.0
expense_items = ss.get("expense_categories", []) or []
if expense_items:
    expenses = sum(e.get("amount", 0) for e in expense_items)
else:
    expenses = ss.get("expenses", 0.0) or 0.0


def loan_details(loan):
    """Months to repay and total interest for one loan (None, None if it never gets repaid)."""
    principal = loan.get("principal", 0)
    rate = loan.get("rate", 9.0)
    payment = loan.get("payment", 0)
    if principal <= 0 or payment <= 0:
        return None, None
    months = months_to_repay(principal, rate, payment)
    if not months:
        return None, None
    schedule = amortisation_schedule(principal, rate, payment, months)
    interest = sum(m["interest_portion"] for m in schedule)
    return months, interest


# ---------- summary cards ----------
details = [loan_details(l) for l in loans]
total_owed = sum(l.get("principal", 0) for l in loans)
total_payment = sum(l.get("payment", 0) for l in loans)
total_interest = sum(d[1] for d in details if d[1] is not None)

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1:
    stat_card("ml_count", t("Loans"), len(loans))
with c2:
    stat_card("ml_owed", t("Total owed"), money(total_owed))
with c3:
    stat_card("ml_paying", t("Paying per month"), money(total_payment))
with c4:
    stat_card("ml_interest", t("Total interest to pay"), money(total_interest))

st.write("")

tab1, tab2, tab3 = st.tabs([t("My loans"), t("Pay off faster"), t("How much can I borrow?")])

# =====================================================================
# TAB 1 - my loans: add, view, remove
# =====================================================================
with tab1:
    with st.container(key="card_add_loan"):
        st.markdown(f'<p class="card-title">{t("Add a loan")}</p>', unsafe_allow_html=True)
        with st.form("add_loan_form", clear_on_submit=True):
            f1, f2 = st.columns(2)
            with f1:
                new_name = st.text_input(t("Loan name"), placeholder="Car loan")
                new_principal = st.number_input(t("Amount still owed (Rs)"), min_value=0.0, step=1000.0)
            with f2:
                new_rate = st.number_input(t("Yearly interest rate (%)"), min_value=0.0,
                                           max_value=100.0, value=9.0, step=0.5)
                new_payment = st.number_input(t("Monthly payment (Rs)"), min_value=0.0, step=100.0)
            submitted = st.form_submit_button(t("Add loan"), type="primary")

        if submitted:
            name = new_name.strip()
            if not name:
                st.error(t("Please give the loan a name."))
            elif any(l["name"].lower() == name.lower() for l in loans):
                st.error(t("You already have a loan with that name."))
            elif new_principal <= 0:
                st.error(t("Loan amount must be greater than 0."))
            else:
                loans.append({
                    "name": name,
                    "principal": new_principal,
                    "rate": new_rate,
                    "payment": new_payment,
                })
                st.rerun()

    st.write("")

    if not loans:
        with st.container(key="card_no_loans"):
            st.info(t("You haven't added any loans yet — add one above."))
    else:
        st.subheader(t("🏦 Your Loans"))

        remove_index = None
        for i, loan in enumerate(loans):
            months, interest = details[i]
            principal = loan.get("principal", 0)
            rate = loan.get("rate", 9.0)
            payment = loan.get("payment", 0)

            with st.container(key=f"card_loan_{i}"):
                if payment <= 0:
                    status = badge("warn", t("No payment set"))
                elif months is None:
                    status = badge("bad", t("Payment too low"))
                else:
                    status = badge("good", t("On track"))

                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;">'
                    f'<p class="card-title" style="font-size:1.2rem;">{loan["name"]}</p>{status}</div>'
                    f'<p class="muted">{t("Owing")}: {money(principal)} · {t("Rate")}: {rate}% · '
                    f'{t("Paying")}: {money(payment)}{t("/month")}</p>',
                    unsafe_allow_html=True
                )

                if payment <= 0:
                    st.warning(t("Set a monthly payment for this loan to see when it will be paid off."))
                elif months is None:
                    st.error(t("⚠️ Your current payment doesn't cover the interest — at this rate, you'll never pay off this loan."))
                else:
                    m1, m2, m3 = st.columns(3)
                    m1.metric(t("Paid off in"), f"{months} {t('months')}")
                    m2.metric(t("Years"), f"{months / 12:.1f}")
                    m3.metric(t("Total interest"), money(interest))

                if st.button(t("Remove"), key=f"remove_loan_{i}", icon=":material/delete:"):
                    remove_index = i

            st.write("")

        if remove_index is not None:
            loans.pop(remove_index)
            st.rerun()

# =====================================================================
# TAB 2 - plan how to pay a loan off
# =====================================================================
with tab2:
    if not loans:
        with st.container(key="card_plan_empty"):
            st.info(t("Add a loan in the 'My loans' tab first."))
    else:
        with st.container(key="card_loan_plan"):
            plan_title = t("Plan how you'll pay off your loan")
            st.markdown(f'<p class="card-title">{plan_title}</p>', unsafe_allow_html=True)

            loan_names = [l["name"] for l in loans]
            selected_name = st.selectbox(t("Which loan?"), loan_names, key="loan_select")
            selected_loan = next(l for l in loans if l["name"] == selected_name)

            principal = selected_loan["principal"]
            annual_rate = selected_loan.get("rate", 9.0)
            current_payment = selected_loan["payment"]

            st.markdown(
                f'<p class="muted">{t("Owing")} {money(principal)} {t("at")} {annual_rate}%, '
                f'{t("currently paying")} {money(current_payment)}{t("/month")}</p>',
                unsafe_allow_html=True
            )

            desired_years = st.number_input(
                t("By when do you want to pay this off? (years)"),
                min_value=1, max_value=30, step=1, value=5,
                key="loan_payoff_years"
            )

            if principal <= 0:
                st.error(t("Loan amount must be greater than 0."))
            else:
                required_payment = calculate_monthly_payment(principal, annual_rate, desired_years)

                st.info(
                    f"💡 {t('To pay this off in')} {desired_years} {t('years, you would need to pay')} "
                    f"**Rs {required_payment:,.2f}{t('/month')}**."
                )

                if current_payment <= 0:
                    st.warning(t("Enter your current monthly payment on your Finances page to compare."))
                elif current_payment >= required_payment:
                    actual_months = months_to_repay(principal, annual_rate, current_payment)
                    if actual_months:
                        actual_years = actual_months / 12
                        st.success(
                            f"✅ {t('At your current payment of')} Rs {current_payment:,.0f}{t('/month')}, "
                            f"{t('you will actually pay this off in')} **{actual_months} {t('months')}** "
                            f"(~{actual_years:.1f} {t('years')}) — {t('at or ahead of your')} "
                            f"{desired_years}-{t('year goal')}!"
                        )
                else:
                    gap = required_payment - current_payment
                    st.warning(
                        f"⚠️ {t('You are currently paying')} Rs {current_payment:,.0f}{t('/month')}, "
                        f"{t('but you would need Rs')} {required_payment:,.2f}{t('/month to hit your')} "
                        f"{desired_years}-{t('year goal')} — {t('a gap of Rs')} {gap:,.2f}{t('/month')}."
                    )

                    if st.button(t("💡 How can I close this gap?"), key="loan_gap_ai"):
                        with st.spinner(t("Thinking...")):
                            explanation = explain_loan_payoff_plan(
                                selected_name, principal, annual_rate, desired_years,
                                required_payment, current_payment, expense_items
                            )
                        st.info(explanation)

        # chart based on the payment they're ACTUALLY making
        if principal > 0 and current_payment > 0:
            st.write("")
            with st.container(key="card_loan_chart"):
                st.markdown(f'<p class="card-title">{t("📊 Interest vs. Principal Over Time")}</p>',
                            unsafe_allow_html=True)

                months_for_chart = months_to_repay(principal, annual_rate, current_payment)
                if months_for_chart:
                    schedule = amortisation_schedule(principal, annual_rate, current_payment, months_for_chart)
                    interest_data = [m["interest_portion"] for m in schedule]
                    principal_data = [m["principal_portion"] for m in schedule]

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(y=interest_data, mode="lines",
                                             name=t("Interest paid (Rs)"), line=dict(width=3)))
                    fig.add_trace(go.Scatter(y=principal_data, mode="lines",
                                             name=t("Principal paid (Rs)"), line=dict(width=3)))
                    fig.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10), height=340,
                        xaxis_title=t("Month"), yaxis_title=t("Rs"),
                        legend=dict(orientation="h", y=1.1)
                    )
                    st.plotly_chart(style_fig(fig), use_container_width=True, key="loan_chart")
                    st.caption(
                        f"{t('Showing the full')} {len(interest_data)}-"
                        f"{t('month repayment period, from month 1 to month')} {len(interest_data)}."
                    )
                else:
                    st.error(t("⚠️ Your current payment doesn't cover the interest — at this rate, you'll never pay off this loan."))

# =====================================================================
# TAB 3 - how much can I borrow?
# =====================================================================
with tab3:
    if "loan2_debt" not in ss:
        ss["loan2_debt"] = float(total_payment)

    with st.container(key="card_borrow"):
        st.markdown(f'<p class="card-title">{t("How much can I realistically borrow?")}</p>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<p class="muted">{t("Using your profile: income")} {money(income)}, '
            f'{t("expenses")} {money(expenses)}</p>',
            unsafe_allow_html=True
        )

        age = st.number_input(t("Your age"), min_value=18, max_value=100, step=1, key="loan2_age")
        existing_debt = st.number_input(
            t("Any existing debt payments? (Rs/month)"),
            min_value=0.0, step=100.0, key="loan2_debt"
        )
        credit_score = st.slider(t("Estimated credit score"), 300, 850, 680, key="loan2_credit")

        predict_clicked = st.button(t("Predict my borrowing power"), type="primary")

    if predict_clicked:
        if income <= 0:
            st.error(t("Please fill in your income on the Your Finances page first."))
        else:
            predicted = predict_max_loan(income, expenses, existing_debt, credit_score, age)

            st.write("")
            with st.container(key="card_borrow_result"):
                st.success(
                    f"📊 {t('Based on your profile, you could realistically borrow up to')} "
                    f"**Rs {predicted:,.2f}**"
                )

            goals = ss.get("goals", []) or []
            savings_rate = ss.get("savings_rate", 0.0)
            current_savings = ss.get("current_savings", 0.0)
            monthly_savings = ss.get("monthly_savings", 0.0)

            if goals:
                st.write("")
                st.subheader(t("🎯 How this could help your goals"))

                for i, goal in enumerate(goals):
                    deadline_months = goal["years"] * 12
                    gap_info = calculate_goal_gap(
                        current_savings, monthly_savings, savings_rate,
                        deadline_months, goal["amount"]
                    )

                    with st.container(key=f"card_loan_goal_{i}"):
                        if gap_info["gap"] <= 0:
                            st.success(
                                f"✅ {t('You are on track to fully save for')} **{goal['name']}** "
                                f"{t('without needing a loan.')}"
                            )
                        else:
                            loan_plan = plan_goal_with_loan(gap_info["gap"], predicted)
                            with st.spinner(f"{t('Thinking about')} {goal['name']}..."):
                                explanation = explain_goal_with_loan(goal, gap_info, loan_plan, predicted)
                            st.info(f"**{goal['name']}**: {explanation}")
                    st.write("")