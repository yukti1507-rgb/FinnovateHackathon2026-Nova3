import streamlit as st
from calculations.projections import run_full_simulation

st.set_page_config(
    page_title="Your Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Your Financial Future")

if "income" not in st.session_state:
    st.warning("Please fill in your details first.")
    st.stop()

results = run_full_simulation(st.session_state, months=60)

# --- Goal verdicts FIRST — this is the headline answer ---
if "goals_status" in results:
    st.subheader("🎯 Your Goals")

    for goal in results["goals_status"]:
        if goal["reached"]:
            st.success(f"✅ **{goal['name']}**: reached in month {goal['month_reached']} (target was month {goal['deadline_months']})")
        else:
            needed = results["required_monthly_per_goal"][goal["name"]]
            st.warning(f"⚠️ **{goal['name']}**: won't reach Rs {goal['amount']} by month {goal['deadline_months']} at your current rate. You'd need Rs {needed}/month instead.")
else:
    st.info("You haven't added any goals yet — go to your Profile page to add one.")

st.divider()

# --- Chart second — supporting evidence ---
st.subheader("📈 Your Savings Projection")
st.line_chart([m["balance"] for m in results["savings_projection"]])

# --- Loan info stays as-is ---
if "loan_summary" in results:
    st.metric("Total interest on loan", f"Rs {results['loan_summary']['total_interest']}")