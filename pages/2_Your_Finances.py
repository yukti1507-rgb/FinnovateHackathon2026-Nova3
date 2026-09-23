import streamlit as st
from calculations.language import show_language_picker, t

st.set_page_config(
    page_title="Your Finances",
    page_icon="👤",
    layout="wide"
)

show_language_picker()

def sanity_check_amount(value, field_label_key, max_reasonable=100_000_000):
    """
    Catches accidental huge numbers -- most commonly from someone
    typing scientific notation by mistake (e.g. typing "5e" while
    aiming for "5000" produces 50,000,000,000 instead). Number inputs
    allow this by default and there's no way to block the keystroke,
    so we flag it after the fact instead of silently accepting it.
    """
    if value > max_reasonable:
        st.warning(
            f"⚠️ {t('That amount looks unusually large for')} {t(field_label_key)} "
            f"({value:,.0f}). {t('Please double-check you did not accidentally use scientific notation (like 5e10) or add an extra digit.')}"
        )

st.title(t("Your Finances"))
st.caption(t("Edit your details anytime — your dashboard updates automatically."))

if "current_savings" not in st.session_state:
    st.session_state["current_savings"] = 0.0
if "monthly_savings" not in st.session_state:
    st.session_state["monthly_savings"] = 0.0
if "savings_rate" not in st.session_state:
    st.session_state["savings_rate"] = 3.0
if "income" not in st.session_state:
    st.session_state["income"] = 0.0
if "goals" not in st.session_state:
    st.session_state["goals"] = []
if "loans" not in st.session_state:
    st.session_state["loans"] = []
if "subscriptions" not in st.session_state:
    st.session_state["subscriptions"] = []
if "variable_expenses" not in st.session_state:
    st.session_state["variable_expenses"] = []
if "other_fixed_expenses" not in st.session_state:
    st.session_state["other_fixed_expenses"] = []

st.write("DEBUG:", dict(st.session_state))  # TEMPORARY - remove after debugging

st.divider()

# ---------- Income ----------
st.subheader(t("💵 Income"))

st.session_state["income"] = st.number_input(
    t("What's your monthly income (take-home)?"),
    min_value=0.0, step=100.0,
    value=st.session_state["income"]
)
income = st.session_state["income"]

st.divider()

# ---------- Reusable row helper ----------
def expense_row(label, key, step=25.0, default_is_need=True, help_text=None):
    if f"{key}_amount" not in st.session_state:
        st.session_state[f"{key}_amount"] = 0.0

    col1, col2 = st.columns([3, 1])
    with col1:
        amount = st.number_input(
            label, min_value=0.0, step=step,
            value=st.session_state[f"{key}_amount"],
            help=help_text
        )
        st.session_state[f"{key}_amount"] = amount
    with col2:
        st.write("")
        is_need = st.toggle("Need", value=default_is_need, key=f"{key}_need")
    return amount, is_need

# ---------- Fixed single-item expenses ----------
st.subheader(t("🧾 Fixed Monthly Expenses"))
st.caption(t("Costs everyone typically has one of."))

rent, rent_is_need = expense_row(t("Rent / mortgage"), "fixed_rent", step=50.0)
insurance, insurance_is_need = expense_row(t("Insurance (health, car, life)"), "fixed_insurance")
utilities, utilities_is_need = expense_row(t("Utilities (electricity, water, phone, internet)"), "fixed_utilities")
school_childcare, school_childcare_is_need = expense_row(t("School / childcare fees"), "fixed_school_childcare", step=50.0)
transport_fixed, transport_fixed_is_need = expense_row(t("Transport pass / lease (bus pass, car lease)"), "fixed_transport")

single_fixed_total = rent + insurance + utilities + school_childcare + transport_fixed

st.divider()

# ---------- Loans (list) ----------
st.subheader(t("🏦 Loans"))
st.caption(t("Add each loan you're currently repaying — e.g. Car, House."))

for i, loan in enumerate(st.session_state["loans"]):
    with st.expander(f"{loan['name']} — Rs {loan['payment']}/month"):
        new_name = st.text_input(t("Loan name"), value=loan["name"], key=f"loan_name_{i}")
        new_principal = st.number_input(
            t("Amount still owed (Rs)"), value=loan["principal"], min_value=0.0, step=500.0, key=f"loan_principal_{i}"
        )
        new_rate = st.slider(
            t("Interest rate (%)"), 0.0, 20.0, value=loan.get("rate", 9.0), step=0.1, key=f"loan_rate_{i}"
        )
        new_payment = st.number_input(
            t("Monthly payment (Rs)"), value=loan["payment"], min_value=0.0, step=50.0, key=f"loan_payment_{i}"
        )

        if new_payment <= 0:
            st.warning(t("⚠️ Payment must be greater than 0 — this loan won't be included until fixed."))
        else:
            st.session_state["loans"][i] = {
                "name": new_name, "principal": new_principal, "rate": new_rate, "payment": new_payment
            }

        if st.button(t("🗑️ Remove this loan"), key=f"remove_loan_{i}"):
            st.session_state["loans"].pop(i)
            st.rerun()

with st.expander(t("➕ Add a loan")):
    new_loan_name = st.text_input(t("What's this loan for?"), placeholder="e.g. Car, House", key="new_loan_name")
    new_loan_principal = st.number_input(t("Amount still owed (Rs)"), min_value=0.0, step=500.0, key="new_loan_principal")
    sanity_check_amount(new_loan_principal, "loan amount")
    new_loan_rate = st.slider(t("Interest rate (%)"), 0.0, 20.0, 9.0, step=0.1, key="new_loan_rate")

    # We already have principal + rate right here, so calculate a
    # suggested minimum payment (standard 5-year term) and pre-fill
    # the payment field with it -- the user only needs to change it
    # if they want to pay MORE than this suggested amount.
    if new_loan_principal > 0:
        from calculations.loans import calculate_monthly_payment
        suggested_new_loan_payment = calculate_monthly_payment(new_loan_principal, new_loan_rate, term_years=5)
        st.caption(f"💡 {t('Suggested minimum payment (5-year term):')} Rs {suggested_new_loan_payment:,.2f}{t('/month')}")
    else:
        suggested_new_loan_payment = 0.0

    new_loan_payment = st.number_input(
        t("Monthly payment (Rs)"), min_value=0.0, step=50.0,
        value=suggested_new_loan_payment, key="new_loan_payment"
    )

    if st.button(t("Add loan"), type="primary"):
        if new_loan_name.strip() == "":
            st.error(t("Please name this loan."))
        elif new_loan_payment <= 0:
            st.error(t("Monthly payment must be greater than 0."))
        else:
            st.session_state["loans"].append({
                "name": new_loan_name, "principal": new_loan_principal,
                "rate": new_loan_rate, "payment": new_loan_payment
            })
            st.success(f"{t('Added')} '{new_loan_name}'!")
            st.rerun()

loans_total = sum(loan["payment"] for loan in st.session_state["loans"])
st.metric(t("Total loan repayments"), f"{loans_total:,.0f}")
st.divider()

# ---------- Subscriptions (list) ----------
st.subheader(t("📺 Subscriptions"))
st.caption(t("Add each subscription — e.g. Netflix, Gym."))

for i, sub in enumerate(st.session_state["subscriptions"]):
    with st.expander(f"{sub['name']} — Rs {sub['amount']}"):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_name = st.text_input(t("Subscription name"), value=sub["name"], key=f"sub_name_{i}")
            new_amount = st.number_input(
                t("Amount (Rs)"), value=sub["amount"], min_value=0.0, step=10.0, key=f"sub_amount_{i}"
            )
        with col2:
            st.write("")
            new_is_need = st.toggle("Need", value=sub["type"] == "Need", key=f"sub_need_{i}")

        if new_amount <= 0:
            st.warning(t("⚠️ Amount must be greater than 0 — this won't be included until fixed."))
        else:
            st.session_state["subscriptions"][i] = {
                "name": new_name, "amount": new_amount, "type": "Need" if new_is_need else "Want"
            }

        if st.button(t("🗑️ Remove"), key=f"remove_sub_{i}"):
            st.session_state["subscriptions"].pop(i)
            st.rerun()

with st.expander(t("➕ Add a subscription")):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_sub_name = st.text_input(t("What's this subscription?"), placeholder="e.g. Netflix, Gym", key="new_sub_name")
        new_sub_amount = st.number_input(t("Amount (Rs)"), min_value=0.0, step=10.0, key="new_sub_amount")
    with col2:
        st.write("")
        new_sub_is_need = st.toggle("Need", value=False, key="new_sub_need")

    if st.button(t("Add subscription"), type="primary"):
        if new_sub_name.strip() == "":
            st.error(t("Please name this subscription."))
        elif new_sub_amount <= 0:
            st.error(t("Amount must be greater than 0."))
        else:
            st.session_state["subscriptions"].append({
                "name": new_sub_name, "amount": new_sub_amount, "type": "Need" if new_sub_is_need else "Want"
            })
            st.success(f"{t('Added')} '{new_sub_name}'!")
            st.rerun()

subscriptions_total = sum(sub["amount"] for sub in st.session_state["subscriptions"])
st.metric(t("Total subscriptions"), f"{subscriptions_total:,.0f}")

st.divider()

# ---------- Other fixed costs (list) ----------
st.markdown(f"**{t('Other fixed costs')}**")
st.caption(t("Any other recurring cost that's the same amount every month."))

for i, expense in enumerate(st.session_state["other_fixed_expenses"]):
    with st.expander(f"{expense['name']} — Rs {expense['amount']}"):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_name = st.text_input(t("Description"), value=expense["name"], key=f"other_fixed_name_{i}")
            new_amount = st.number_input(
                t("Amount (Rs)"), value=expense["amount"], min_value=0.0, step=25.0, key=f"other_fixed_amount_{i}"
            )
        with col2:
            st.write("")
            new_is_need = st.toggle("Need", value=expense["type"] == "Need", key=f"other_fixed_need_{i}")

        if new_amount <= 0:
            st.warning(t("⚠️ Amount must be greater than 0 — this won't be included until fixed."))
        else:
            st.session_state["other_fixed_expenses"][i] = {
                "name": new_name, "amount": new_amount, "type": "Need" if new_is_need else "Want"
            }

        if st.button(t("🗑️ Remove"), key=f"remove_other_fixed_{i}"):
            st.session_state["other_fixed_expenses"].pop(i)
            st.rerun()

with st.expander(t("➕ Add another fixed cost")):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_of_name = st.text_input(t("What's this cost?"), key="new_other_fixed_name")
        new_of_amount = st.number_input(t("Amount (Rs)"), min_value=0.0, step=25.0, key="new_other_fixed_amount")
    with col2:
        st.write("")
        new_of_is_need = st.toggle("Need", value=True, key="new_other_fixed_need")

    if st.button(t("Add cost"), type="primary"):
        if new_of_name.strip() == "":
            st.error(t("Please describe this cost."))
        elif new_of_amount <= 0:
            st.error(t("Amount must be greater than 0."))
        else:
            st.session_state["other_fixed_expenses"].append({
                "name": new_of_name, "amount": new_of_amount, "type": "Need" if new_of_is_need else "Want"
            })
            st.success(f"{t('Added')} '{new_of_name}'!")
            st.rerun()

other_fixed_total = sum(e["amount"] for e in st.session_state["other_fixed_expenses"])

fixed_total = single_fixed_total + loans_total + subscriptions_total + other_fixed_total

st.divider()

# ---------- Variable / day-to-day expenses (list) ----------
st.subheader(t("🛒 Day-to-Day & Variable Expenses"))
st.caption(t("Add each variable cost individually — e.g. 'Market' 2000, 'Takeout' 300."))

for i, expense in enumerate(st.session_state["variable_expenses"]):
    with st.expander(f"{expense['name']} — Rs {expense['amount']}"):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_name = st.text_input(t("Description"), value=expense["name"], key=f"var_name_{i}")
            new_amount = st.number_input(
                t("Amount (Rs)"), value=expense["amount"], min_value=0.0, step=50.0, key=f"var_amount_{i}"
            )
        with col2:
            st.write("")
            new_is_need = st.toggle("Need", value=expense["type"] == "Need", key=f"var_need_{i}")

        if new_amount <= 0:
            st.warning(t("⚠️ Amount must be greater than 0 — this won't be included until fixed."))
        else:
            st.session_state["variable_expenses"][i] = {
                "name": new_name, "amount": new_amount, "type": "Need" if new_is_need else "Want"
            }

        if st.button(t("🗑️ Remove"), key=f"remove_var_{i}"):
            st.session_state["variable_expenses"].pop(i)
            st.rerun()

with st.expander(t("➕ Add a variable expense")):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_var_name = st.text_input(t("What was it for?"), key="new_var_name_input", placeholder="e.g. Market, Takeout, Fuel")
        new_var_amount = st.number_input(t("Amount (Rs)"), min_value=0.0, step=50.0, key="new_var_amount_input")
    with col2:
        st.write("")
        new_var_is_need = st.toggle("Need", value=False, key="new_var_need_input")

    if st.button(t("Add expense"), type="primary"):
        if new_var_name.strip() == "":
            st.error(t("Please describe this expense."))
        elif new_var_amount <= 0:
            st.error(t("Amount must be greater than 0."))
        else:
            st.session_state["variable_expenses"].append({
                "name": new_var_name, "amount": new_var_amount, "type": "Need" if new_var_is_need else "Want"
            })
            st.success(f"{t('Added')} '{new_var_name}'!")
            st.rerun()

variable_total = sum(e["amount"] for e in st.session_state["variable_expenses"])
st.metric(t("Total variable expenses"), f"{variable_total:,.0f}")

st.divider()

expenses = fixed_total + variable_total
st.session_state["expenses"] = expenses

fixed_categories = [
    {"name": "Rent/Mortgage", "amount": rent, "type": "Need" if rent_is_need else "Want"},
    {"name": "Insurance", "amount": insurance, "type": "Need" if insurance_is_need else "Want"},
    {"name": "Utilities", "amount": utilities, "type": "Need" if utilities_is_need else "Want"},
    {"name": "School/childcare", "amount": school_childcare, "type": "Need" if school_childcare_is_need else "Want"},
    {"name": "Transport (fixed)", "amount": transport_fixed, "type": "Need" if transport_fixed_is_need else "Want"},
] + st.session_state["other_fixed_expenses"]

loan_categories = [{"name": f"Loan: {l['name']}", "amount": l["payment"], "type": "Need"} for l in st.session_state["loans"]]
subscription_categories = [{"name": s["name"], "amount": s["amount"], "type": s["type"]} for s in st.session_state["subscriptions"]]

st.session_state["expense_categories"] = (
    fixed_categories + loan_categories + subscription_categories + st.session_state["variable_expenses"]
)

col_e1, col_e2 = st.columns(2)
with col_e1:
    st.metric(t("Total monthly expenses"), f"{expenses:,.0f}")
with col_e2:
    available = income - expenses
    st.metric(t("Available after expenses"), f"{available:,.0f}")

if income > 0 and expenses > income:
    st.warning(t("⚠️ Your expenses currently exceed your income — there's nothing left over to save."))

st.divider()

st.subheader(t("🏦 Savings"))

st.session_state["current_savings"] = st.number_input(
    t("How much do you currently have saved?"),
    min_value=0.0, step=100.0,
    value=st.session_state["current_savings"]
)

available = income - expenses

if not st.session_state.get("monthly_savings_touched", False) and available > 0:
    st.session_state["monthly_savings"] = available

st.session_state["monthly_savings"] = st.number_input(
    t("How much would you like to save each month?"),
    min_value=0.0, step=100.0,
    value=st.session_state["monthly_savings"],
    help=f"You have about Rs {available:,.0f} available after expenses."
)
st.session_state["monthly_savings_touched"] = True

if st.session_state["monthly_savings"] > available:
    st.warning(
        f"⚠️ You've set your savings target to Rs {st.session_state['monthly_savings']:,.0f}/month, "
        f"but only Rs {available:,.0f} is actually available after your expenses. "
        f"Your goal calculations may be based on an unrealistic number."
    )

st.session_state["savings_rate"] = st.slider(
    t("Expected annual interest rate on your savings (%)"),
    0.0, 10.0,
    value=st.session_state["savings_rate"],
    step=0.1
)

st.divider()

st.subheader(t("🎯 Your Goals"))

# BUG FIX: goal widgets used to be keyed by their LIST POSITION (i).
# When a goal in the middle/start of the list was deleted, every
# goal after it shifted position -- but Streamlit remembers widget
# values BY KEY, so the shifted goal's box would still show the
# PREVIOUS goal's stale data at that position, instead of its own.
#
# Fix: give every goal a permanent, stable "id" that never changes,
# and key widgets by that id instead of by position. New goals get
# the next id from an ever-increasing counter, so ids are never
# reused even after deletions.
if "goal_id_counter" not in st.session_state:
    st.session_state["goal_id_counter"] = 0

for g in st.session_state["goals"]:
    if "id" not in g:
        g["id"] = st.session_state["goal_id_counter"]
        st.session_state["goal_id_counter"] += 1

for i, goal in enumerate(st.session_state["goals"]):
    gid = goal["id"]
    with st.expander(f"{goal['name']} — Rs {goal['amount']}"):
        new_name = st.text_input(t("Goal name"), value=goal["name"], key=f"goal_name_{gid}")
        new_amount = st.number_input(
            t("Amount needed (Rs)"), value=goal["amount"], min_value=0.0, step=500.0, key=f"goal_amount_{gid}"
        )
        new_years = st.number_input(
            t("Years to achieve"), value=goal["years"], min_value=1, max_value=30, step=1, key=f"goal_years_{gid}"
        )

        if new_amount <= 0:
            st.warning(t("⚠️ Amount must be greater than 0 — this goal won't be included in calculations until fixed."))
        else:
            st.session_state["goals"][i] = {"name": new_name, "amount": new_amount, "years": new_years, "id": gid}

        if st.button(t("🗑️ Remove this goal"), key=f"remove_goal_{gid}"):
            st.session_state["goals"].pop(i)
            st.rerun()

st.write("")

with st.expander(t("➕ Add a new goal")):
    st.info(
        f"\U0001f4a1 {t('This is for SAVING toward something (a car, a trip, emergency fund, etc.).')} "
        f"{t('If your goal is to pay off an existing loan or debt, use the Loans page instead — it calculates this more accurately.')}"
    )
    if st.button(t("\U0001f4b3 Go to Loans page"), key="goto_loans_from_goal"):
        st.switch_page("pages/4_Loans.py")

    new_goal_name = st.text_input(t("What are you saving for?"), key="new_goal_name_input")
    new_goal_amount = st.number_input(t("How much do you need? (Rs)"), min_value=0.0, step=500.0, key="new_goal_amount_input")
    sanity_check_amount(new_goal_amount, "goal amount")
    new_goal_years = st.number_input(t("By when? (years from now)"), min_value=1, max_value=30, step=1, key="new_goal_years_input")

    if st.button(t("Add goal"), type="primary"):
        if new_goal_name.strip() == "":
            st.error(t("Please give your goal a name."))
        elif new_goal_amount <= 0:
            st.error(t("Goal amount must be greater than 0."))
        else:
            st.session_state["goals"].append({
                "name": new_goal_name, "amount": new_goal_amount, "years": new_goal_years,
                "id": st.session_state["goal_id_counter"]
            })
            st.session_state["goal_id_counter"] += 1

            # BUG FIX: the Add-goal form's own input boxes were
            # never being cleared after a successful add -- Streamlit
            # remembers typed values by key forever unless you
            # explicitly remove them. This is why the SAME name/amount
            # kept reappearing every time the "Add a new goal" section
            # was reopened, even after deleting that goal.
            for key_to_clear in ["new_goal_name_input", "new_goal_amount_input", "new_goal_years_input"]:
                st.session_state.pop(key_to_clear, None)

            st.success(f"{t('Added')} '{new_goal_name}' {t('to your goals!')}")
            st.rerun()

st.divider()

if st.button(t("📊 View my Dashboard"), type="primary"):
    st.switch_page("pages/3_Dashboard.py")