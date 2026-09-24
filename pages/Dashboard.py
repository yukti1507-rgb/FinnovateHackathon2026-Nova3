# pages/Dashboard.py - main page after login
# Reads live data from st.session_state (same source as the Goals / Forecast pages)

import datetime as dt
import pandas as pd
import streamlit as st
from calculations.projections import run_full_simulation
from ui import (apply_theme, navbar, require_login, page_header, tile, money, safe_link,
                TILE_PAGES, FINANCES_PAGE, GOALS_PAGE, FORECAST_PAGE,
                DEEP, BLUE, MIST, NAVY, SKY, TEXT, CARD, POS, NEG)

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")
apply_theme()
require_login()
navbar(active="Dashboard")

username = st.session_state.get("username")

# Find the Loans page file automatically (any .py with "loan" in its name)
from pathlib import Path


def _find_loans_page():
    here = Path(__file__).resolve().parent
    for folder in (here, here / "pages"):
        if folder.is_dir():
            for f in sorted(folder.glob("*.py")):
                if "loan" in f.name.lower():
                    return f"pages/{f.name}"
    return "pages/loans.py"


MY_LOANS_PAGE = _find_loans_page()

# Set to True if your loan payments are NOT already inside "expense_categories"
INCLUDE_LOANS_IN_EXPENSES = False

GOAL_COLUMNS = ["Goal", "Target", "Saved", "Monthly saving", "Months left", "Status"]
TX_COLUMNS = ["date", "name", "category", "amount"]


# ------------------------------------------------------------------
# DATA - built from st.session_state (filled in on the Finances page)
# ------------------------------------------------------------------
def load_dashboard_data(username):
    ss = st.session_state
    today = dt.date.today()

    # ---- income / expenses ----
    monthly_income = ss.get("income", 0) or 0
    expense_items = ss.get("expense_categories", []) or []
    monthly_expenses = sum(e.get("amount", 0) for e in expense_items)
    if INCLUDE_LOANS_IN_EXPENSES:
        monthly_expenses += sum(l.get("payment", 0) for l in (ss.get("loans", []) or []))

    # ---- goals: same simulation the Goals page uses ----
    goals_rows = []
    if "income" in ss:
        try:
            results = run_full_simulation(ss, months=60)
        except Exception:
            results = {}
        for g in results.get("goals_status") or []:
            name = g["name"]
            months = results["actual_months_per_goal"].get(name)
            if g["reached"]:
                status, months_left = "Reached", 0
            elif months is not None:
                status, months_left = "Behind", months
            else:
                status, months_left = "Out of reach", None
            goals_rows.append({
                "Goal": name,
                "Target": g["amount"],
                "Saved": min(ss.get("current_savings", 0) or 0, g["amount"]),
                "Monthly saving": results["required_monthly_per_goal"].get(name, 0),
                "Months left": months_left,
                "Status": status,
            })
    goals = pd.DataFrame(goals_rows, columns=GOAL_COLUMNS)

    # ---- "transactions": built from what the user entered (no history stored) ----
    rows = []
    if monthly_income:
        rows.append({"date": today, "name": "Monthly income",
                     "category": "Income", "amount": monthly_income})
    for e in expense_items:
        if e.get("amount", 0) > 0:
            rows.append({"date": today, "name": e.get("name", "Expense"),
                         "category": "Expense", "amount": -e["amount"]})
    if INCLUDE_LOANS_IN_EXPENSES:
        for l in (ss.get("loans", []) or []):
            if l.get("payment", 0) > 0:
                rows.append({"date": today, "name": l.get("name", "Loan"),
                             "category": "Loan", "amount": -l["payment"]})
    transactions = pd.DataFrame(rows, columns=TX_COLUMNS)

    return {
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "total_savings": ss.get("current_savings", 0) or 0,
        "transactions": transactions,
        "goals": goals,
    }


data = load_dashboard_data(username)
income = data["monthly_income"]
expenses = data["monthly_expenses"]
net = income - expenses
save_rate = (net / income * 100) if income else 0

# ---------- Welcome ----------
page_header(f"Welcome back, {username}",
            dt.datetime.now().strftime("%A %d %B %Y"))
st.write("")

# ---------- Icon tiles (act as buttons) ----------
tiles = [list(x) for x in TILE_PAGES]
_loan_icon = ":material/account_balance:" if (tiles and str(tiles[0][2]).startswith(":material")) else "🏦"
_has_loan_tile = False
for _tl in tiles:
    if "loan" in str(_tl[0]).lower():      # existing Loans tile -> send it to the Loans page
        _tl[1] = MY_LOANS_PAGE
        _has_loan_tile = True
if not _has_loan_tile:                     # no Loans tile yet -> add one
    tiles.append(["Loans", MY_LOANS_PAGE, _loan_icon, "Track what you owe"])

for col, (label, path, icon, blurb) in zip(st.columns(len(tiles)), tiles):
    with col:
        tile(label, path, icon, blurb, key=label.lower())

st.write("")

# ---------- Row 1: money card  |  total savings ----------
left, right = st.columns([1.9, 1], gap="medium")

with left:
    with st.container(key="card_account"):
        st.markdown('<p class="card-title">This month</p>', unsafe_allow_html=True)
        card_col, add_col = st.columns([2.2, 1])
        with card_col:
            st.markdown(f"""
<div style="position:relative; height:190px; margin-top:8px;">
  <div style="position:absolute; left:18px; top:0; right:0; height:170px; border-radius:18px;
              background:{SKY}; opacity:.55;"></div>
  <div style="position:absolute; left:0; top:16px; right:18px; height:170px; border-radius:18px;
              padding:18px 22px; color:#fff; overflow:hidden;
              background: radial-gradient(circle at 85% 30%, {BLUE} 0 28%, transparent 29%),
                          linear-gradient(135deg, {NAVY}, {DEEP});">
    <div style="display:flex; justify-content:space-between; font-size:.8rem; opacity:.85;">
      <span>Net savings</span><span>Saving rate {save_rate:.0f}%</span>
    </div>
    <div style="font-size:2rem; font-weight:800; margin-top:18px;">{money(net)}</div>
    <div style="display:flex; justify-content:space-between; margin-top:26px; font-size:.85rem;">
      <span>In {money(income)}</span><span>Out {money(expenses)}</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
        with add_col:
            with st.container(key="tile_addincome"):
                safe_link(FINANCES_PAGE, "Add income", ":material/add_circle:")
                st.caption("Log a new payment")

with right:
    with st.container(key="card_balance"):
        st.markdown(f"""
<div style="text-align:center;">
  <p class="card-title">Your total savings</p>
  <div style="font-size:2.3rem; font-weight:800; color:{DEEP}; margin:10px 0 4px;">{money(data['total_savings'])}</div>
  <div class="muted">{dt.datetime.now().strftime('%d %B %Y, %H:%M')}</div>
</div>""", unsafe_allow_html=True)
        st.write("")
        with st.container(key="quick"):
            q1, q2, q3 = st.columns(3)
            with q1:
                safe_link(GOALS_PAGE, "Goals", ":material/flag:")
            with q2:
                safe_link(MY_LOANS_PAGE, "Loans", ":material/account_balance:")
            with q3:
                safe_link(FORECAST_PAGE, "Forecast", ":material/trending_up:")

st.write("")

# ---------- Row 2: recent transactions  |  spending gauge ----------
left, right = st.columns([1.9, 1], gap="medium")

with left:
    with st.container(key="card_transactions"):
        h1, h2 = st.columns([2, 1])
        with h1:
            st.markdown('<p class="card-title">Recent transactions</p>', unsafe_allow_html=True)
        with h2:
            days = st.selectbox("Period", [7, 30, 90], format_func=lambda d: f"Last {d} days",
                                label_visibility="collapsed")

        tx = data["transactions"]
        if not tx.empty:
            tx = tx[tx["date"] >= dt.date.today() - dt.timedelta(days=days)].sort_values(
                "date", ascending=False)

        icons = {"Income": "↓", "Expense": "🛍", "Need": "🏠", "Want": "🛍", "Loan": "🏦"}
        if tx.empty:
            st.info("No transactions in this period. Add some on the Your Finances page.")
        for _, r in tx.head(5).iterrows():
            colour = POS if r["amount"] > 0 else NEG
            sign = "+" if r["amount"] > 0 else "−"
            st.markdown(f"""
<div style="display:flex; align-items:center; gap:14px; padding:10px 0; border-bottom:1px solid {MIST};">
  <div style="width:42px; height:42px; border-radius:12px; background:{MIST};
              display:grid; place-items:center; font-size:1.1rem; color:{DEEP};">{icons.get(r['category'], '•')}</div>
  <div style="flex:1;">
    <div style="font-weight:600; color:{TEXT};">{r['name']}</div>
    <div class="muted">{r['date'].strftime('%d %b %Y')} · {r['category']}</div>
  </div>
  <div style="font-weight:700; color:{colour};">{sign} {money(abs(r['amount']))}</div>
</div>""", unsafe_allow_html=True)

with right:
    with st.container(key="card_gauge"):
        spent_pct = min(expenses / income * 100, 100) if income else 0
        deg = spent_pct * 1.8   # 100% = half circle = 180deg
        if spent_pct < 50:
            level = "Healthy"
        elif spent_pct < 80:
            level = "Normal"
        else:
            level = "High"
        st.markdown(f"""
<p class="card-title">Spending vs income</p>
<div style="display:flex; flex-direction:column; align-items:center; margin-top:14px;">
  <div style="position:relative; width:220px; height:110px; overflow:hidden;">
    <div style="width:220px; height:220px; border-radius:50%;
                background: conic-gradient(from -90deg, {DEEP} 0deg {deg}deg, {MIST} {deg}deg 180deg, transparent 180deg);"></div>
    <div style="position:absolute; left:32px; top:32px; width:156px; height:156px; border-radius:50%; background:{CARD};"></div>
    <div style="position:absolute; left:0; right:0; bottom:4px; text-align:center;">
      <div style="font-size:1.8rem; font-weight:800; color:{TEXT};">{spent_pct:.1f}%</div>
      <div style="color:{BLUE}; font-weight:600; font-size:.9rem;">{level} level</div>
    </div>
  </div>
  <div style="margin-top:18px; background:{MIST}; border-radius:12px; padding:8px 16px; font-size:.9rem; color:{TEXT};">
    Total spent: <b>{money(expenses)}</b>
  </div>
</div>""", unsafe_allow_html=True)

st.write("")

# ---------- Row 3: goals table ----------
with st.container(key="card_goals"):
    h1, h2, h3 = st.columns([2, 1.2, 0.6])
    with h1:
        st.markdown('<p class="card-title">Goal activity</p>', unsafe_allow_html=True)
    with h2:
        search = st.text_input("Search goals", placeholder="Search…", label_visibility="collapsed")
    goals = data["goals"]
    if search and not goals.empty:
        goals = goals[goals["Goal"].str.contains(search, case=False, na=False)]
    with h3:
        st.download_button("Export", goals.to_csv(index=False), "goals.csv", "text/csv",
                           icon=":material/download:")

    if goals.empty:
        st.info("No goals yet. Add one on the Your Finances page and it will show up here.")
    else:
        target = pd.to_numeric(goals["Target"], errors="coerce").replace(0, pd.NA)
        saved = pd.to_numeric(goals["Saved"], errors="coerce")
        progress = (saved / target).fillna(0).astype(float).clip(0, 1)
        goals = goals.assign(Progress=progress)
        st.dataframe(
            goals,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Target": st.column_config.NumberColumn(format="Rs %d"),
                "Saved": st.column_config.NumberColumn(format="Rs %d"),
                "Monthly saving": st.column_config.NumberColumn(format="Rs %d"),
                "Progress": st.column_config.ProgressColumn(min_value=0, max_value=1, format="percent"),
            },
        )