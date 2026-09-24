from calculations.savings import project_savings

def required_monthly_contribution(goal_amount, current_savings, annual_rate, months):
    """
    Rearranged compound interest formula — solves for the monthly
    contribution needed to reach a goal by a deadline.
    """
    if months is None or months <= 0:
        return 0.0

    monthly_rate = annual_rate / 100 / 12

    if monthly_rate == 0:
        # no interest — simple division
        return round((goal_amount - current_savings) / months, 2)

    future_value_of_current_savings = current_savings * (1 + monthly_rate) ** months
    remaining_needed = goal_amount - future_value_of_current_savings

    if remaining_needed <= 0:
        return 0.0  # already on track without saving more

    annuity_factor = ((1 + monthly_rate) ** months - 1) / monthly_rate
    monthly_needed = remaining_needed / annuity_factor

    return round(monthly_needed, 2)

def will_reach_goal(goal_amount, current_savings, monthly_contribution, annual_rate, months):
    """
    Checks if a given savings plan reaches the goal in time, and if so, when.
    """
    history = project_savings(current_savings, monthly_contribution, annual_rate, months)

    for entry in history:
        if entry["balance"] >= goal_amount:
            return {"reached": True, "month_reached": entry["month"]}

    return {"reached": False, "month_reached": None}

def check_all_goals(savings_history, goals):
    """
    Checks each goal against a shared savings history.

    Prefer target_date-derived months_remaining/years_remaining.
    Legacy goals may still have years only; this fallback is retained
    only for compatibility with older records.
    """
    results = []

    for goal in goals:
        from calculations.goal_allocation import resolve_goal_deadline_months

        goal_name = goal.get("name") or goal.get("goal_name") or "Goal"
        goal_amount = goal.get("amount")
        if goal_amount is None:
            goal_amount = goal.get("target_amount")
        if goal_amount is None:
            goal_amount = 0

        goal = {
            **goal,
            "name": goal_name,
            "amount": goal_amount,
            "goal_name": goal_name,
            "target_amount": goal_amount,
        }

        goal_months = goal.get("months_remaining")
        if goal_months is None:
            goal_months = resolve_goal_deadline_months(goal)

        goal_months = max(int(goal_months or 0), 0)

        years_for_inflation = goal.get("years_remaining")
        if years_for_inflation is None:
            if goal.get("target_date") is not None:
                years_for_inflation = (goal_months / 12) if goal_months else 0
            else:
                years_for_inflation = float(goal.get("years", 0) or 0)

        if goal_months == 0:
            real_target = inflation_adjusted_target(goal["amount"], years_for_inflation)
            reached_month = 0 if savings_history and savings_history[-1]["balance"] >= real_target else None
        else:
            real_target = inflation_adjusted_target(goal["amount"], years_for_inflation)
            reached_month = None
            for entry in savings_history:
                if entry["month"] > goal_months:
                    break
                if entry["balance"] >= real_target:
                    reached_month = entry["month"]
                    break

        results.append({
            "name": goal["name"],
            "amount": goal["amount"],
            "real_target": real_target,
            "deadline_months": goal_months,
            "reached": reached_month is not None,
            "month_reached": reached_month
        })

    return results

def months_to_reach_at_current_rate(current_savings, monthly_savings, annual_rate, target_amount, max_months=600):
    """
    Projects savings forward (ignoring any deadline) to find out how
    long it would ACTUALLY take to reach the goal at their current rate.
    Returns the month number, or None if it's not reachable within
    max_months (50 years) — e.g. if monthly_savings is 0 or too low.
    """
    from calculations.savings import project_savings

    history = project_savings(current_savings, monthly_savings, annual_rate, max_months)

    for entry in history:
        if entry["balance"] >= target_amount:
            return entry["month"]

    return None  # not reachable within 50 years at this rate

def calculate_goal_gap(current_savings, monthly_savings, annual_rate, deadline_months, target_amount):
    """
    Projects savings up to the goal's deadline (not open-ended) and
    calculates the shortfall against the target.
    """
    from calculations.savings import project_savings

    history = project_savings(current_savings, monthly_savings, annual_rate, deadline_months)
    savings_by_deadline = history[-1]["balance"] if history else current_savings

    gap = target_amount - savings_by_deadline
    return {
        "savings_by_deadline": round(savings_by_deadline, 2),
        "gap": round(max(gap, 0), 2)
    }

def inflation_adjusted_target(target_amount, years, inflation_rate=0.05):
    """
    Calculates what a goal will actually cost by the time the user
    reaches their deadline, accounting for price inflation — not
    just today's price. `years` should be the CURRENT years
    remaining until the deadline, not a static original duration --
    callers should derive this fresh from target_date each time.
    """
    return round(target_amount * (1 + inflation_rate) ** years, 2)

def inflating_target_over_time(target_amount, deadline_months, inflation_rate=0.05):
    """
    Returns the inflating target value for EVERY month up to the
    deadline, so it can be plotted as a rising line on a chart
    alongside the savings balance line.
    """
    monthly_inflation = (1 + inflation_rate) ** (1/12) - 1  # convert annual rate to monthly
    return [
        round(target_amount * (1 + monthly_inflation) ** month, 2)
        for month in range(1, deadline_months + 1)
    ]

def find_best_cuts(user_data, goals_status, cut_percent=0.5):
    """
    Tests cutting each 'want' expense by cut_percent, and finds which
    cut helps a goal the most. Pure calculation — AI only narrates this.
    """
    from calculations.projections import run_full_simulation

    wants = [e for e in user_data.get("expense_categories", []) if e["type"] == "Want" and e["amount"] > 0]
    suggestions = []

    for want in wants:
        cut_amount = want["amount"] * cut_percent

        adjusted_data = dict(user_data)
        adjusted_data["monthly_savings"] = user_data["monthly_savings"] + cut_amount

        adjusted_results = run_full_simulation(adjusted_data, months=60)
        adjusted_goals = adjusted_results.get("goals_status", [])

        for goal in goals_status:
            old_month = goal["month_reached"]
            matching = next((g for g in adjusted_goals if g["name"] == goal["name"]), None)
            new_month = matching["month_reached"] if matching else None

            if old_month and new_month and new_month < old_month:
                suggestions.append({
                    "expense_name": want["name"],
                    "expense_amount": want["amount"],
                    "cut_amount": round(cut_amount, 2),
                    "goal_name": goal["name"],
                    "months_saved": old_month - new_month
                })

    suggestions.sort(key=lambda s: s["months_saved"], reverse=True)
    return suggestions
