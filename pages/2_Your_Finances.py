import streamlit as st
from main import profile_icon

st.set_page_config(
    page_title="Your Finances",
    page_icon="💰",
    layout="wide"
)

col1, col2 = st.columns([1, 3])
with col1:
    st.title("Tell us about your finances")
with col2:
    profile_icon()

st.caption(
    "Fill in what applies to you — leave anything at 0 if it doesn't apply. "
    "Everything here feeds into your projection on the Dashboard."
)

st.divider()

# ---------- Income ----------
st.subheader("💵 Income")
income = st.number_input(
    "What's your monthly income (take-home)?",
    min_value=0.0, step=100.0, key="income_input"
)

st.divider()

# ---------- Fixed / recurring expenses ----------
st.subheader("🧾 Fixed Monthly Expenses")
st.caption("Costs that stay roughly the same every month.")

fixed_defaults = {
    "fixed_rent": 0.0,
    "fixed_loan_repayment": 0.0,
    "fixed_insurance": 0.0,
    "fixed_utilities": 0.0,
    "fixed_subscriptions": 0.0,
    "fixed_school_childcare": 0.0,
    "fixed_transport": 0.0,
    "fixed_other": 0.0,
}
for key, val in fixed_defaults.items():
    st.session_state.setdefault(key, val)

fcol1, fcol2 = st.columns(2)
with fcol1:
    st.markdown("**🏠 Housing & Loans**")
    rent = st.number_input("Rent / mortgage", min_value=0.0, step=50.0, key="fixed_rent")
    loan_repayment = st.number_input(
        "Loan repayments (car, student, personal)", min_value=0.0, step=50.0,
        key="fixed_loan_repayment",
        help="If you also fill in the Loan section further down, only enter the repayment here once — don't double it up."
    )
    insurance = st.number_input("Insurance (health, car, life)", min_value=0.0, step=25.0, key="fixed_insurance")

with fcol2:
    st.markdown("**📺 Recurring Commitments**")
    utilities = st.number_input(
        "Utilities (electricity, water, phone, internet)", min_value=0.0, step=25.0, key="fixed_utilities"
    )
    subscriptions = st.number_input(
        "Subscriptions (streaming, gym, software)", min_value=0.0, step=10.0, key="fixed_subscriptions"
    )
    school_childcare = st.number_input(
        "School / childcare fees", min_value=0.0, step=50.0, key="fixed_school_childcare"
    )
    transport_fixed = st.number_input(
        "Transport pass / lease (bus pass, car lease)", min_value=0.0, step=25.0, key="fixed_transport"
    )

other_fixed = st.number_input(
    "Other fixed costs", min_value=0.0, step=25.0, key="fixed_other",
    help="Any other recurring cost that's the same amount every month."
)

fixed_total = (
    rent + loan_repayment + insurance + utilities
    + subscriptions + school_childcare + transport_fixed + other_fixed
)
st.metric("Total fixed expenses", f"{fixed_total:,.0f}")

st.divider()

# ---------- Variable / day-to-day expenses ----------
st.subheader("🛒 Day-to-Day & Variable Expenses")
st.caption("Costs that change from month to month.")

st.markdown("**Food & groceries**")
food_type = st.selectbox(
    "Is this spending a need or a want?",
    ["Need (e.g. groceries, home cooking)", "Want (e.g. takeout, snacks, treats)"],
    key="food_type"
)
food = st.number_input(
    "How much do you spend on this per month?", min_value=0.0, step=50.0, key="food_amount"
)
food_is_need = food_type.startswith("Need")

extra_transport = st.number_input(
    "Other transport (fuel, taxis, occasional rides)", min_value=0.0, step=25.0,
    key="variable_transport",
    help="For day-to-day fuel or ride costs — a bus pass or car lease is captured above under Fixed Expenses."
)
other_variable = st.number_input(
    "Other variable expenses", min_value=0.0, step=50.0, key="variable_other",
    help="Anything not covered above — e.g. clothing, gifts, medical, pet costs."
)

variable_total = food + extra_transport + other_variable
st.metric("Total variable expenses", f"{variable_total:,.0f}")

st.divider()

expenses = fixed_total + variable_total

col_e1, col_e2 = st.columns(2)
with col_e1:
    st.metric("Total monthly expenses", f"{expenses:,.0f}")
with col_e2:
    available = income - expenses
    st.metric("Available after expenses", f"{available:,.0f}")

if income > 0 and expenses > income:
    st.warning("⚠️ Your expenses currently exceed your income — there's nothing left over to save.")

st.divider()

# ---------- Savings ----------
st.subheader("🏦 Savings")
current_savings = st.number_input(
    "How much do you currently have saved?", min_value=0.0, step=100.0, key="current_savings_input"
)
monthly_savings = st.number_input(
    "How much would you like to save each month?", min_value=0.0, step=100.0, key="monthly_savings_input"
)
savings_rate = st.slider(
    "Expected annual interest rate on your savings (%)", 0.0, 10.0, 3.0, step=0.1,
    help="The average return your savings account or investment earns per year.",
    key="savings_rate_input"
)

if monthly_savings > available:
    st.warning(
        f"⚠️ You're planning to save {monthly_savings:,.0f} but only have {available:,.0f} available after expenses."
    )

st.divider()

# ---------- Loan ----------
st.subheader("💳 Loan")
st.caption(
    "If you're repaying a loan and want it modeled in your projection, fill this in. "
    "This is separate from the repayment amount you entered above — that's for your monthly budget, this is for the payoff timeline."
)
has_loan = st.radio(
    "Do you have a loan you're currently repaying?", ["No", "Yes"], horizontal=True, key="has_loan_input"
)

loan_amount = 0.0
loan_rate = 0.0
loan_term_years = 0

if has_loan == "Yes":
    loan_amount = st.number_input("How much did you borrow?", min_value=0.0, step=500.0, key="loan_amount_input")
    loan_rate = st.slider("What's the interest rate (%)?", 0.0, 20.0, 9.0, step=0.1, key="loan_rate_input")
    loan_term_years = st.number_input(
        "Over how many years are you repaying it?", min_value=1, max_value=30, step=1, key="loan_term_input"
    )

st.divider()

# ---------- Savings Goal ----------
st.subheader("🎯 Savings Goal")
has_goal = st.radio(
    "Are you saving toward a specific goal?", ["No", "Yes"], horizontal=True, key="has_goal_input"
)

goal_name = ""
goal_amount = 0.0
goal_years = 0

if has_goal == "Yes":
    goal_name = st.text_input("What are you saving for? (e.g. Car, Emergency fund, Trip)", key="goal_name_input")
    goal_amount = st.number_input("How much do you need?", min_value=0.0, step=500.0, key="goal_amount_input")
    goal_years = st.number_input("By when? (years from now)", min_value=1, max_value=30, step=1, key="goal_years_input")

st.divider()

# ---------- Run simulation ----------
if st.button("Run my simulation", type="primary"):
    st.session_state["income"] = income

    st.session_state["fixed_expenses"] = fixed_total
    st.session_state["variable_expenses"] = variable_total
    st.session_state["food"] = food
    st.session_state["food_is_need"] = food_is_need
    st.session_state["expenses"] = expenses

    st.session_state["current_savings"] = current_savings
    st.session_state["monthly_savings"] = monthly_savings
    st.session_state["savings_rate"] = savings_rate

    st.session_state["has_loan"] = has_loan == "Yes"
    st.session_state["loan_amount"] = loan_amount
    st.session_state["loan_rate"] = loan_rate
    st.session_state["loan_term_years"] = loan_term_years

    st.session_state["has_goal"] = has_goal == "Yes"
    st.session_state["goal_name"] = goal_name
    st.session_state["goal_amount"] = goal_amount
    st.session_state["goal_years"] = goal_years

    st.success("Got it! Heading to Dashboard to see your projection.")
    st.switch_page("pages/3_Dashboard.py")

