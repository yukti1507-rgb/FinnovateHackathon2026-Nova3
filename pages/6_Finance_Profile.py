import streamlit as st
import plotly.graph_objects as go
from calculations.language import show_language_picker, t
from calculations.projections import run_full_simulation
from calculations.loans import amortisation_schedule
from calculations.goals import inflating_target_over_time
from calculations.goals_ai import explain_loan_repayment

st.set_page_config(
    page_title="Finance Profile",
    page_icon="📊",
    layout="wide"
)

show_language_picker()

st.title(t("📊 Your Finance Profile"))
st.caption(t("A snapshot of your spending, loans, and goals — all in one place."))

if "income" not in st.session_state:
    st.warning(t("Please fill in your details first."))
    st.stop()

results = run_full_simulation(st.session_state, months=60)

# ============================================================
# Row 1: Spending breakdown (pie) + Loan repayment (line)
# ============================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader(t("💸 Where Your Money Goes"))

    expense_categories = st.session_state.get("expense_categories", [])

    if expense_categories:
        # group small amounts isn't needed here since names are already distinct
        names = [e["name"] for e in expense_categories if e["amount"] > 0]
        amounts = [e["amount"] for e in expense_categories if e["amount"] > 0]

        if amounts:
            fig = go.Figure(data=[go.Pie(
                labels=names,
                values=amounts,
                hole=0.45,  # donut style
                textinfo="percent",
                hovertemplate="%{label}: Rs %{value:,.0f}<extra></extra>"
            )])
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t("Add some expenses on your Finances page to see this chart."))
    else:
        st.info(t("Add some expenses on your Finances page to see this chart."))

with col2:
    st.subheader(t("💳 Loan Repayment"))

    loans = st.session_state.get("loans", [])

    if loans:
        loan_names = [l["name"] for l in loans]
        selected_loan_name = st.selectbox(t("Which loan?"), loan_names, key="profile_loan_select")
        selected_loan = next(l for l in loans if l["name"] == selected_loan_name)

        principal = selected_loan["principal"]
        annual_rate = selected_loan.get("rate", 9.0)
        monthly_payment = selected_loan["payment"]

        if principal > 0 and monthly_payment > 0:
            from calculations.loans import months_to_repay
            months = months_to_repay(principal, annual_rate, monthly_payment)

            if months:
                schedule = amortisation_schedule(principal, annual_rate, monthly_payment, months)
                interest_data = [m["interest_portion"] for m in schedule]
                principal_data = [m["principal_portion"] for m in schedule]

                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    y=interest_data, mode="lines", name=t("Interest paid (Rs)"),
                    line=dict(width=3)
                ))
                fig2.add_trace(go.Scatter(
                    y=principal_data, mode="lines", name=t("Principal paid (Rs)"),
                    line=dict(width=3)
                ))
                fig2.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis_title=t("Month"),
                    yaxis_title=t("Rs")
                )
                st.plotly_chart(fig2, use_container_width=True)

                total_interest = sum(m["interest_portion"] for m in schedule)

                if st.button(t("💡 Explain this loan"), key="explain_loan_btn"):
                    with st.spinner(t("Thinking...")):
                        explanation = explain_loan_repayment(
                            selected_loan_name, principal, annual_rate,
                            monthly_payment, months, round(total_interest, 2)
                        )
                    st.info(explanation)
            else:
                st.warning(t("This loan's payment doesn't cover the interest — check the Loans page."))
        else:
            st.info(t("This loan needs a valid amount and payment — check the Loans page."))
    else:
        st.info(t("Add a loan on your Finances page to see this chart."))

st.divider()

# ============================================================
# Row 2: Goal progress (full width)
# ============================================================
st.subheader(t("🎯 Your Goals vs. Inflation-Adjusted Targets"))

if "goals_status" in results and results["goals_status"]:
    goal_names = [g["name"] for g in results["goals_status"]]
    selected_goal_name = st.selectbox(t("Which goal?"), goal_names, key="profile_goal_select")
    selected_goal = next(g for g in results["goals_status"] if g["name"] == selected_goal_name)

    deadline_months = selected_goal["deadline_months"]
    savings_for_this_goal = [m["balance"] for m in results["savings_projection"][:deadline_months]]
    inflating_line = inflating_target_over_time(selected_goal["amount"], deadline_months)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        y=savings_for_this_goal, mode="lines", name=t("Your savings"),
        line=dict(width=3)
    ))
    fig3.add_trace(go.Scatter(
        y=inflating_line, mode="lines", name=t("Inflating target"),
        line=dict(width=3, dash="dash")
    ))
    fig3.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis_title=t("Month"),
        yaxis_title=t("Rs"),
        height=400
    )
    st.plotly_chart(fig3, use_container_width=True)

    if selected_goal["reached"]:
        st.success(f"✅ {t('Reached in month')} {selected_goal['month_reached']}")
    else:
        st.warning(f"⚠️ {t('Not yet reached by your deadline of month')} {deadline_months}")
else:
    st.info(t("You haven't added any goals yet — go to your Finances page to add one."))