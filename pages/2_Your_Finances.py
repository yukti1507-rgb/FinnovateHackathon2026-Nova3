import streamlit as st

st.set_page_config(
    page_title="Your Profile",
    page_icon="👤",
    layout="wide"
)

st.title("Your Profile")
st.caption("Edit your details anytime — your dashboard updates automatically.")

# ----------------------------------------------------------------
# STEP 1: Set up default values in session_state (only runs once,
# the first time this page ever loads — after that, session_state
# already has these keys, so this block is skipped)
# ----------------------------------------------------------------
if "income" not in st.session_state:
    st.session_state["income"] = 0.0
if "expenses" not in st.session_state:
    st.session_state["expenses"] = 0.0
if "current_savings" not in st.session_state:
    st.session_state["current_savings"] = 0.0
if "monthly_savings" not in st.session_state:
    st.session_state["monthly_savings"] = 0.0
if "savings_rate" not in st.session_state:
    st.session_state["savings_rate"] = 3.0
if "goals" not in st.session_state:
    st.session_state["goals"] = []  # empty list — no goals yet

# ----------------------------------------------------------------
# STEP 2: Income & Expenses — editable inputs
# The `value=` parameter pre-fills the box with whatever is already
# saved, so returning users see their existing numbers, not blanks.
# Every time a value changes, we immediately write it back to
# session_state — no "submit" button needed for this section.
# ----------------------------------------------------------------
st.subheader("💵 Income & Expenses")

st.session_state["income"] = st.number_input(
    "What's your monthly income?",
    min_value=0.0, step=100.0,
    value=st.session_state["income"]
)

st.session_state["expenses"] = st.number_input(
    "Roughly how much do you spend per month on essentials?",
    min_value=0.0, step=100.0,
    value=st.session_state["expenses"]
)

st.divider()

# ----------------------------------------------------------------
# STEP 3: Savings — same editable pattern
# ----------------------------------------------------------------
st.subheader("🏦 Savings")

st.session_state["current_savings"] = st.number_input(
    "How much do you currently have saved?",
    min_value=0.0, step=100.0,
    value=st.session_state["current_savings"]
)

st.session_state["monthly_savings"] = st.number_input(
    "How much would you like to save each month?",
    min_value=0.0, step=100.0,
    value=st.session_state["monthly_savings"]
)

st.session_state["savings_rate"] = st.slider(
    "Expected annual interest rate on your savings (%)",
    0.0, 10.0,
    value=st.session_state["savings_rate"],
    step=0.1
)

st.divider()

# ----------------------------------------------------------------
# STEP 4: Goals — this is the multi-goal section
# st.session_state["goals"] is a LIST of dicts, e.g.:
# [{"name": "Laptop", "amount": 45000, "years": 1}, ...]
# ----------------------------------------------------------------
st.subheader("🎯 Your Goals")

# --- show each existing goal, editable, with a remove button ---
# enumerate() gives us both the index (i) and the goal dict itself,
# so we can update or delete the correct one in the list.
for i, goal in enumerate(st.session_state["goals"]):

    # each goal gets its own collapsible box, labelled with its name/amount
    with st.expander(f"{goal['name']} — Rs {goal['amount']}"):

        # NOTE: every widget here needs a UNIQUE key (using i).
        # Without unique keys, Streamlit can't tell these text boxes
        # apart from the ones in the next loop iteration, and it'll
        # throw a duplicate-element error.
        new_name = st.text_input(
            "Goal name", value=goal["name"], key=f"goal_name_{i}"
        )
        new_amount = st.number_input(
            "Amount needed (Rs)", value=goal["amount"],
            min_value=0.0, step=500.0, key=f"goal_amount_{i}"
        )
        new_years = st.number_input(
            "Years to achieve", value=goal["years"],
            min_value=1, max_value=30, step=1, key=f"goal_years_{i}"
        )

        # write the (possibly edited) values straight back into the list
        if new_amount <= 0:
            st.warning("⚠️ Amount must be greater than 0 — this goal won't be included in calculations until fixed.")
        else:
            st.session_state["goals"][i] = {
                "name": new_name,
                "amount": new_amount,
                "years": new_years
            }

        # remove button — deletes this goal and refreshes the page
        if st.button("🗑️ Remove this goal", key=f"remove_goal_{i}"):
            st.session_state["goals"].pop(i)
            st.rerun()  # re-run the page so the removed goal disappears immediately

st.write("")  # small spacing gap

# --- form to add a brand new goal ---
with st.expander("➕ Add a new goal"):
    new_goal_name = st.text_input("What are you saving for?", key="new_goal_name_input")
    new_goal_amount = st.number_input(
        "How much do you need? (Rs)", min_value=0.0, step=500.0, key="new_goal_amount_input"
    )
    new_goal_years = st.number_input(
        "By when? (years from now)", min_value=1, max_value=30, step=1, key="new_goal_years_input"
    )

    if st.button("Add goal", type="primary"):
        if new_goal_name.strip() == "":
            st.error("Please give your goal a name.")
        elif new_goal_amount <= 0:
            st.error("Goal amount must be greater than 0.")
        else:
            st.session_state["goals"].append({
                "name": new_goal_name,
                "amount": new_goal_amount,
                "years": new_goal_years
            })
            st.success(f"Added '{new_goal_name}' to your goals!")
            st.rerun()

st.divider()

# ----------------------------------------------------------------
# STEP 5: Link to the Dashboard
# No "Run simulation" button needed anymore — everything above
# already saved live into session_state as you typed. This button
# just navigates you to see the results.
# ----------------------------------------------------------------
if st.button("📊 View my Dashboard", type="primary"):
    st.switch_page("pages/3_Dashboard.py")