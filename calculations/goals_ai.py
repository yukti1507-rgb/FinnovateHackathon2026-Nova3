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
    to lay out the user's actual OPTIONS: save more, cut a specific
    expense, or take a loan. The AI only narrates — every number here
    was already calculated by pure Python functions above/elsewhere.
    """
    increased_amount = round(monthly_savings * (1 + increase_percent), 2)

    lang = st.session_state.get("language", "en")
    lang_name = {"en": "English", "fr": "French"}.get(lang, "English")

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

    # ---- Option C: rough loan estimate for any goal with a real shortfall ----
    loan_options_text = ""
    for goal in goals_status:
        if not goal["reached"]:
            deadline_months = goal["deadline_months"]
            target_for_gap = goal.get("real_target", goal["amount"])
            gap_info = calculate_goal_gap(
                user_data["current_savings"], user_data["monthly_savings"],
                user_data["savings_rate"], deadline_months, target_for_gap
            )
            if gap_info["gap"] > 0:
                rough_payment = calculate_monthly_payment(gap_info["gap"], 9.0, 5)
                loan_options_text += (
                    f"For '{goal['name']}', a loan of about Rs {gap_info['gap']} at ~9% over 5 years "
                    f"would cost roughly Rs {rough_payment}/month. "
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

    Option C — take a loan: {loan_options_text if loan_options_text else "No goal currently has a shortfall requiring a loan."}

    In 4-5 friendly, clear sentences: briefly mention that these numbers
    account for inflation (so the goals will genuinely cost more by the
    time they're reached, not just today's price), then lay out the real
    OPTIONS the user can choose between (not a single forced
    recommendation) — saving more, cutting a specific expense, or taking
    a loan — using ONLY the numbers given above. Do not invent or
    recalculate anything yourself. If an option has no real effect
    (marked as such above), skip it rather than forcing it into the answer.

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

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Sorry, I couldn't generate an explanation right now — please try again in a moment."