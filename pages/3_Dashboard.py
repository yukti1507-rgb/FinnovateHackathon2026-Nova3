import streamlit as st
from calculations.projections import run_full_simulation
from calculations.goals_ai import simulate_savings_increase, explain_goals
from calculations.language import show_language_picker, t
from calculations.goals import inflating_target_over_time

st.set_page_config(
    page_title="Your Dashboard",
    page_icon="📊",
    layout="wide"
)

show_language_picker()

st.title(t("Your Financial Future"))

if "income" not in st.session_state:
    st.warning(t("Please fill in your details first."))
    st.stop()

results = run_full_simulation(st.session_state, months=60)

if "goals_status" in results:
    st.subheader(t("🎯 Your Goals"))

    for goal in results["goals_status"]:
        actual_months = results["actual_months_per_goal"][goal["name"]]
        real_target = results["inflation_adjusted_target_per_goal"][goal["name"]]

        if goal["reached"]:
            st.caption(f"💡 {t('With inflation, this goal will likely cost around')} Rs {real_target:,.0f} {t('by your deadline (vs. Rs')} {goal['amount']:,.0f} {t('today).')}")
            st.success(f"✅ **{goal['name']}**: {t('reached in month')} {goal['month_reached']} ({t('target was month')} {goal['deadline_months']})")
        else:
            needed = results["required_monthly_per_goal"][goal["name"]]

            if actual_months is not None:
                st.caption(f"💡 {t('With inflation, this goal will likely cost around')} Rs {real_target:,.0f} {t('by your deadline (vs. Rs')} {goal['amount']:,.0f} {t('today).')}")
                st.warning(
                    f"⚠️ **{goal['name']}**: {t('at your current savings trend, you would reach')} Rs {goal['amount']:,.0f} {t('in')} **{actual_months} {t('months')}** — "
                    f"{t('that is later than your')} {goal['deadline_months']}-{t('month target')}. "
                    f"{t('To hit your deadline, try saving')} Rs {needed:,.2f} {t('per month instead')}. "
                    f"{t('If that is not doable right now, you might consider a loan to cover the gap.')}"
                )
            else:
                st.error(
                    f"🚨 **{goal['name']}**: {t('at your current rate, this goal is not reachable within 50 years.')} "
                    f"{t('You would need to save')} Rs {needed:,.2f} {t('per month to hit your')} {goal['deadline_months']}-{t('month target')} — "
                    f"{t('a loan may be worth considering if that is out of reach.')}"
                )

        with st.expander(f"📈 {t('See')} {goal['name']} {t('vs. inflation-adjusted target')}"):
            deadline_months = goal["deadline_months"]

            # savings balance for just this goal's timeframe (trim the 60-month projection)
            savings_for_this_goal = [
                m["balance"] for m in results["savings_projection"][:deadline_months]
            ]

            # the inflating target line, same length
            inflating_line = inflating_target_over_time(goal["amount"], deadline_months)

            st.line_chart({
                t("Your savings"): savings_for_this_goal,
                t("Inflating target"): inflating_line
            })
else:
    st.info(t("You haven't added any goals yet — go to your Finances page to add one."))


st.divider()

if "goals_status" in results:
    if st.button(t("💡 Explain my results")):
        with st.spinner(t("Thinking...")):
            adjusted_goals = simulate_savings_increase(st.session_state, increase_percent=0.10)
            explanation = explain_goals(
                results["goals_status"],
                adjusted_goals,
                results["actual_months_per_goal"],
                results["required_monthly_per_goal"],
                st.session_state["monthly_savings"],
                dict(st.session_state),
                results["inflation_adjusted_target_per_goal"]
            )
        st.info(explanation)
st.divider()

st.subheader(t("📈 Your Savings Projection"))
st.line_chart([m["balance"] for m in results["savings_projection"]])

if "loan_summary" in results:
    st.metric(t("Total interest on loan"), f"Rs {results['loan_summary']['total_interest']}")