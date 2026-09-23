import streamlit as st
from groq import Groq
from calculations.projections import run_full_simulation

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


def explain_goals(goals_status, adjusted_goals_status, actual_months_per_goal, required_monthly_per_goal, monthly_savings, increase_percent=0.10):
    """
    Hands the REAL, already-calculated numbers to the AI and asks it
    to explain them in plain language, including whether a loan might
    help close a large gap.
    """
    increased_amount = round(monthly_savings * (1 + increase_percent), 2)

    lang = st.session_state.get("language", "en")
    lang_name = {"en": "English", "fr": "French"}.get(lang, "English")

    prompt = f"""
    A user's current goal progress: {goals_status}

    At their current savings rate, here's how long each goal would
    ACTUALLY take (ignoring their deadline): {actual_months_per_goal}

    Here's what they'd need to save monthly to hit their actual deadline
    instead: {required_monthly_per_goal}

    If they increased their monthly savings by {int(increase_percent * 100)}%
    (from Rs {monthly_savings} to Rs {increased_amount}), their goal
    progress would become: {adjusted_goals_status}

    In 3-4 friendly, encouraging sentences: explain why they will or won't
    reach their goals on time, mention how much sooner saving more would
    help, and — ONLY if the gap between their actual timeline and their
    target is large (e.g. more than double the target time) — gently
    suggest that a loan could be worth considering to close that gap.
    Only use the numbers given above — do not invent or recalculate
    anything yourself.

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
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content