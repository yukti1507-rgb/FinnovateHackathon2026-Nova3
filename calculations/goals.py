from calculations.savings import project_savings

def required_monthly_contribution(goal_amount, current_savings, annual_rate, months):
    """
    Rearranged compound interest formula — solves for the monthly
    contribution needed to reach a goal by a deadline.
    """
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
    Checks each goal against the same savings projection.
    goals = [{"name": ..., "amount": ..., "years": ...}, ...]
    """
    results = []
    for goal in goals:
        goal_months = goal["years"] * 12
        reached_month = None

        for entry in savings_history:
            if entry["month"] > goal_months:
                break
            if entry["balance"] >= goal["amount"]:
                reached_month = entry["month"]
                break

        results.append({
            "name": goal["name"],
            "amount": goal["amount"],
            "deadline_months": goal_months,
            "reached": reached_month is not None,
            "month_reached": reached_month
        })
    return results