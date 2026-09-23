import streamlit as st
from groq import Groq
from calculations.projections import run_full_simulation
from calculations.loans import calculate_monthly_payment
from calculations.goals import calculate_goal_gap, find_best_cuts

# set up the Groq client once, using the API key from secrets.toml
client = Groq(api_key=st.secrets["GROQ_API_KEY"])


def simulate_savings_increase(user_data, increase_percent=0.10):
    """
    Pure calculation — no AI here. Takes the user's current data,
    increases their monthly savings by a percentage, and reruns the
    EXACT SAME simulation function used everywhere else in the app
    (run_full_simulation) to get accurate, consistent goal results.
    """
    # make a copy so we don't accidentally overwrite the user's real data
    adjusted_data = dict(user_data)

    extra_savings = user_data["monthly_savings"] * increase_percent
    adjusted_data["monthly_savings"] = user_data["monthly_savings"] + extra_savings

    adjusted_results = run_full_simulation(adjusted_data, months=60)

    # return just the goals part — that's all explain_goals() needs
    return adjusted_results.get("goals_status", [])


def explain_goals(goals_status, adjusted_goals_status, actual_months_per_goal, required_monthly_per_goal, monthly_savings, user_data, inflation_adjusted_target_per_goal=None, increase_percent=0.10):
    """
    Hands the REAL, already-calculated numbers to the AI and asks it
    to lay out the user's actual OPTIONS for SAVINGS goals: save more,
    or cut a specific expense. The AI only narrates — every number here
    was already calculated by pure Python functions above/elsewhere.

    NOTE: loan suggestions were intentionally removed from this function.
    Goals here are for SAVING TOWARD something (a car, a trip, etc.) --
    paying off an existing loan/debt is a different math problem, handled
    properly on the dedicated Loans page instead. Suggesting "take a loan"
    here previously created nonsensical advice like "take a loan to help
    pay off your mortgage goal."
    """
    increased_amount = round(monthly_savings * (1 + increase_percent), 2)

    lang = st.session_state.get("language", "en")
    lang_name = {"en": "English", "fr": "French", "cr": "Kreol Morisien (Mauritian Creole)"}.get(lang, "English")

    # ---- Option B: best specific expense cut, if any genuinely helps ----
    best_cuts = find_best_cuts(user_data, goals_status)
    top_cut_text = ""
    if best_cuts:
        top = best_cuts[0]
        top_cut_text = (
            f"Cutting '{top['expense_name']}' (currently Rs {top['expense_amount']}/month, a 'want') "
            f"by half would save Rs {top['cut_amount']}/month and reach '{top['goal_name']}' "
            f"{top['months_saved']} months sooner."
        )

    inflation_text = ""
    if inflation_adjusted_target_per_goal:
        inflation_text = (
            f"Important: due to inflation (assumed 5%/year), each goal will actually "
            f"cost MORE by the time the user reaches it than its price today. "
            f"The real, inflation-adjusted cost of each goal by its deadline is: "
            f"{inflation_adjusted_target_per_goal}. All the reached/not-reached results "
            f"above already account for this — they are checked against these inflated "
            f"values, not today's prices."
        )

    prompt = f"""
    A user's current goal progress: {goals_status}

    {inflation_text}

    At their current savings rate, here's how long each goal would
    ACTUALLY take (ignoring their deadline): {actual_months_per_goal}

    Here's what they'd need to save monthly to hit their actual deadline
    instead: {required_monthly_per_goal}

    Option A — save more: increasing monthly savings by {int(increase_percent * 100)}%
    (from Rs {monthly_savings} to Rs {increased_amount}) would change progress to: {adjusted_goals_status}

    Option B — cut a specific expense: {top_cut_text if top_cut_text else "No single want-expense cut meaningfully speeds up any goal."}

    In 3-4 friendly, clear sentences: briefly mention that these numbers
    account for inflation (so the goals will genuinely cost more by the
    time they're reached, not just today's price), then lay out the real
    OPTIONS the user can choose between (not a single forced
    recommendation) — saving more, or cutting a specific expense —
    using ONLY the numbers given above. Do not invent or recalculate
    anything yourself. Do NOT suggest taking out a loan under any
    circumstances -- that is handled elsewhere in the app. If an option
    has no real effect (marked as such above), skip it rather than
    forcing it into the answer.

    All amounts are in Mauritian Rupees (MUR, symbol "Rs"). Always use
    "Rs" for every amount you mention -- never use $, USD, INR, or any
    other currency symbol or name, and never convert the numbers to
    another currency.

    Respond entirely in {lang_name}.
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Sorry, I couldn't generate an explanation right now — please try again in a moment."


def explain_goal_with_loan(goal, gap_info, loan_plan, max_borrowable):
    lang = st.session_state.get("language", "en")
    lang_name = {"en": "English", "fr": "French", "cr": "Kreol Morisien (Mauritian Creole)"}.get(lang, "English")

    prompt = f"""
    A user's goal: {goal}
    By their deadline, they'll have saved: Rs {gap_info['savings_by_deadline']}
    Shortfall against their target: Rs {gap_info['gap']}
    They could borrow up to: Rs {max_borrowable}
    Loan plan to cover the gap: {loan_plan}

    In 3-4 friendly sentences, explain their situation: how much they'll
    have saved on their own, that a loan can cover the rest, and what
    their monthly loan repayment would look like. If the loan doesn't
    fully cover the gap, say so honestly and suggest they'll need to
    save more or extend their timeline. Only use the numbers given —
    do not invent or recalculate anything.

    All amounts are in Mauritian Rupees (MUR, symbol "Rs"). Always use
    "Rs" for every amount you mention -- never use $, USD, INR, or any
    other currency symbol or name, and never convert the numbers to
    another currency.

    Respond entirely in {lang_name}.
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("EXPLAIN_GOAL_WITH_LOAN ERROR:", repr(e))
        return "Sorry, I couldn't generate an explanation right now — please try again in a moment."


def explain_loan_repayment(loan_name, principal, annual_rate, monthly_payment, months, total_interest):
    """
    Explains a loan's interest-vs-principal pattern in plain language.
    All numbers here are already calculated — the AI only narrates.
    """
    lang = st.session_state.get("language", "en")
    lang_name = {"en": "English", "fr": "French", "cr": "Kreol Morisien (Mauritian Creole)"}.get(lang, "English")

    prompt = f"""
    A user has a loan called '{loan_name}':
    - Amount owed: Rs {principal}
    - Interest rate: {annual_rate}% per year
    - Monthly payment: Rs {monthly_payment}
    - Time to pay off: {months} months
    - Total interest they'll pay over the life of the loan: Rs {total_interest}

    In 2-3 friendly, plain-language sentences, explain to the user:
    why their early payments go more toward interest and later payments go
    more toward the actual balance (if applicable), and what the total
    interest cost means for them in practical terms. Only use the numbers
    given above — do not invent or recalculate anything.

    All amounts are in Mauritian Rupees (MUR, symbol "Rs"). Always use
    "Rs" for every amount you mention -- never use $, USD, INR, or any
    other currency symbol or name, and never convert the numbers to
    another currency.

    Respond entirely in {lang_name}.
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("EXPLAIN_LOAN_REPAYMENT ERROR:", repr(e))  # TEMPORARY - check terminal
        return "Sorry, I couldn't generate an explanation right now — please try again in a moment."


def explain_loan_payoff_plan(loan_name, principal, annual_rate, desired_years, required_payment, current_payment, expense_categories):
    """
    Compares what the user is CURRENTLY paying against what they'd NEED
    to pay to hit their own chosen payoff timeframe, and suggests which
    'want' expenses could realistically cover the gap. All numbers here
    are already calculated -- the AI only narrates and picks the most
    sensible option(s) from the real list given.
    """
    lang = st.session_state.get("language", "en")
    lang_name = {"en": "English", "fr": "French", "cr": "Kreol Morisien (Mauritian Creole)"}.get(lang, "English")

    gap = round(required_payment - current_payment, 2)

    wants = [e for e in expense_categories if e["type"] == "Want" and e["amount"] > 0]
    wants_text = ", ".join(f"{w['name']} (Rs {w['amount']}/month)" for w in wants) if wants else "none listed"

    prompt = f"""
    A user has a loan called '{loan_name}':
    - Amount owed: Rs {principal}
    - Interest rate: {annual_rate}% per year
    - They want to pay it off in {desired_years} years
    - To hit that timeframe, they'd need to pay Rs {required_payment}/month
    - They are CURRENTLY paying: Rs {current_payment}/month
    - Gap between what's needed and what they currently pay: Rs {gap}/month

    Their 'want' expenses (non-essential, could potentially be reduced): {wants_text}

    In 3-4 friendly, clear sentences: if the gap is positive (they need to
    pay MORE to hit their {desired_years}-year goal), suggest ONE OR MORE
    specific 'want' expenses from the list above whose combined amount
    could realistically cover or help cover the gap, and state clearly
    that increasing their payment to Rs {required_payment}/month gets them
    to their goal in exactly {desired_years} years. If the gap is zero or
    negative (they're already paying enough or more), congratulate them
    and confirm they're on track or ahead. Only use the numbers given
    above -- do not invent or recalculate anything yourself.

    All amounts are in Mauritian Rupees (MUR, symbol "Rs"). Always use
    "Rs" for every amount you mention -- never use $, USD, INR, or any
    other currency symbol or name, and never convert the numbers to
    another currency.

    Respond entirely in {lang_name}.
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("EXPLAIN_LOAN_PAYOFF_PLAN ERROR:", repr(e))
        return "Sorry, I couldn't generate an explanation right now — please try again in a moment."


def answer_user_question(question, user_data, results):
    """
    Answers a ONE-OFF question about the user's own financial data.
    NOT a persistent chatbot -- no memory across questions, no
    follow-up conversation. Same guardrail pattern as every other
    function in this file: the AI is handed the user's REAL
    calculated data and told to answer ONLY using it, and to refuse
    anything unrelated (investment advice, stock picks, general life
    advice, anything not about THIS app's own numbers).
    """
    lang = st.session_state.get("language", "en")
    lang_name = {"en": "English", "fr": "French", "cr": "Kreol Morisien (Mauritian Creole)"}.get(lang, "English")

    # gather only what's safe/relevant to hand over -- never invent
    # extra context, just pass through what's already calculated
    goals_status = results.get("goals_status", [])
    loans = user_data.get("loans", [])
    expense_categories = user_data.get("expense_categories", [])
    income = user_data.get("income", 0)
    expenses = user_data.get("expenses", 0)
    current_savings = user_data.get("current_savings", 0)
    monthly_savings = user_data.get("monthly_savings", 0)

    prompt = f"""
    You are a narrow financial-summary assistant INSIDE a specific app.
    You may ONLY answer questions about the user's OWN data shown below.
    You must REFUSE (politely, in 1-2 sentences) any question that is:
    - general investment advice ("what stock should I buy")
    - unrelated to personal finance ("what's the weather")
    - asking for legal/tax/professional advice
    - asking you to calculate something NOT already given below
      (you are not allowed to do new math -- only reference the
      numbers already provided)

    The user's data:
    - Monthly income: Rs {income}
    - Monthly expenses: Rs {expenses}
    - Expense categories: {expense_categories}
    - Current savings: Rs {current_savings}
    - Monthly savings: Rs {monthly_savings}
    - Goals progress: {goals_status}
    - Loans: {loans}

    The user's question: "{question}"

    If the question is answerable using ONLY the data above, answer
    in 2-3 friendly sentences using ONLY those numbers -- do not
    invent or recalculate anything.

    If the question asks for a NEW calculation this data doesn't
    cover (e.g. "what if I saved more?", "what if I paid off my loan
    faster?"), do NOT attempt to calculate it yourself. Instead,
    politely explain that this box can't run new calculations, and
    point them to the specific existing feature that already answers
    that kind of question:
    - "what if I saved more / cut an expense" -> the "Explain my
      results" button on the Dashboard page (next to their goals)
    - "what if I paid more on my loan" -> the Loans page, where they
      can enter a target payoff timeframe
    - "how much could I borrow" -> the "How much can I borrow?" tab
      on the Loans page

    If the question is entirely off-topic (investment advice, stock
    picks, anything unrelated to personal finance in this app),
    politely say this assistant can only help with questions about
    their own goals, loans, and spending shown in the app.

    All amounts are in Mauritian Rupees (MUR, symbol "Rs"). Always use
    "Rs" for every amount you mention -- never use $, USD, INR, or any
    other currency symbol or name, and never convert the numbers to
    another currency.

    Respond entirely in {lang_name}.
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("ANSWER_USER_QUESTION ERROR:", repr(e))
        return "Sorry, I couldn't answer that right now — please try again in a moment."