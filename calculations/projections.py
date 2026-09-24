from calculations.savings import project_savings
from calculations.loans import amortisation_schedule, months_to_repay
from calculations.goals import required_monthly_contribution, check_all_goals, months_to_reach_at_current_rate, inflation_adjusted_target
from calculations.goal_allocation import calculate_months_remaining, resolve_goal_deadline_months

def run_full_simulation(user_data, months=60):
    """
    Takes the dictionary of user inputs (from session_state) and
    returns a full results package: savings projection, loan
    schedules (if applicable), and goal progress (if applicable).
    """
    results = {}

    # --------------------------------------------------------
    # GOALS: normalise deadlines ONCE, here.
    # --------------------------------------------------------
    # target_date is the single source of truth for a goal's
    # deadline (it's a real calendar date in the database).
    # "years"/"months" are always DERIVED fresh from it, never
    # stored or trusted as a static field -- otherwise a goal's
    # remaining time silently goes stale the longer a user goes
    # without logging in.
    # --------------------------------------------------------

    raw_goals = user_data.get("goals")
    goals = None

    if raw_goals:
        goals = []

        for g in raw_goals:
            goal_name = g.get("goal_name") or g.get("name") or "Goal"
            target_amount = g.get("target_amount")
            if target_amount is None:
                target_amount = g.get("amount", 0)

            normalized_goal = {
                **g,
                "name": goal_name,
                "goal_name": goal_name,
                "amount": target_amount,
                "target_amount": target_amount,
                "current_amount": g.get("current_amount", 0),
            }

            months_remaining = resolve_goal_deadline_months(normalized_goal)

            goals.append({
                **normalized_goal,
                "months_remaining": months_remaining,
                "years_remaining": months_remaining / 12
            })

    # --------------------------------------------------------
    # FIX: extend the projection window to cover the furthest
    # goal deadline. Previously fixed at `months` (default 60),
    # so any goal with a deadline beyond 5 years was silently
    # mis-evaluated by check_all_goals() below, since it only
    # ever saw entries up to month 60.
    # --------------------------------------------------------

    if goals:
        max_goal_months = max((g["months_remaining"] for g in goals), default=0)
        months = max(months, max_goal_months)

    # Always run savings projection
    results["savings_projection"] = project_savings(
        starting_balance=user_data["current_savings"],
        monthly_contribution=user_data["monthly_savings"],
        annual_rate=user_data["savings_rate"],
        months=months
    )

    # --------------------------------------------------------
    # LOANS
    # --------------------------------------------------------

    loans = user_data.get("loans", [])

    if loans:
        loan_schedules = {}
        loan_summaries = {}

        total_interest_all_loans = 0
        total_monthly_payment_all_loans = 0

        for loan in loans:
            name = loan.get("name", "Loan")
            principal = loan.get("principal", 0)
            annual_rate = loan.get("interest_rate", 0)
            monthly_payment = loan.get("monthly_payment", 0)

            if principal in (None, 0) or monthly_payment in (None, 0):
                continue

            term_months = months_to_repay(principal, annual_rate, monthly_payment)

            if term_months is None:
                loan_summaries[name] = {
                    "monthly_payment": monthly_payment,
                    "term_months": None,
                    "total_interest": None,
                    "payoff_possible": False
                }
                continue

            schedule = amortisation_schedule(principal, annual_rate, term_months=term_months)
            loan_schedules[name] = schedule

            total_interest = sum(m["interest_portion"] for m in schedule)

            loan_summaries[name] = {
                "monthly_payment": monthly_payment,
                "term_months": term_months,
                "total_interest": round(total_interest, 2),
                "payoff_possible": True
            }

            total_interest_all_loans += total_interest
            total_monthly_payment_all_loans += monthly_payment

        results["loan_schedules"] = loan_schedules
        results["loan_summaries"] = loan_summaries
        results["loan_summary"] = {
            "total_interest": round(total_interest_all_loans, 2),
            "total_monthly_payment": round(total_monthly_payment_all_loans, 2),
            "loan_count": len(loans)
        }

    # --------------------------------------------------------
    # GOALS
    # --------------------------------------------------------

    if goals:
        results["goals_status"] = check_all_goals(results["savings_projection"], goals)

        # What each goal will actually cost by its deadline, with
        # inflation. IMPORTANT: computed FIRST, so every other calc
        # below uses this SAME real (inflation-adjusted) target --
        # never the raw today-price amount. Mixing raw and inflated
        # targets across calculations was causing contradictory
        # messages (e.g. "you'll reach it sooner" alongside "that's
        # later than your target"). years_remaining is derived fresh
        # from target_date above, not a stored static value.
        results["inflation_adjusted_target_per_goal"] = {
            g["name"]: inflation_adjusted_target(g["amount"], g["years_remaining"])
            for g in goals
        }

        results["required_monthly_per_goal"] = {
            g["name"]: required_monthly_contribution(
                results["inflation_adjusted_target_per_goal"][g["name"]],
                user_data["current_savings"],
                user_data["savings_rate"], g["months_remaining"]
            )
            for g in goals
        }

        # actual time to reach each goal's REAL (inflated) target at
        # current rate, no deadline
        results["actual_months_per_goal"] = {
            g["name"]: months_to_reach_at_current_rate(
                user_data["current_savings"], user_data["monthly_savings"],
                user_data["savings_rate"],
                results["inflation_adjusted_target_per_goal"][g["name"]]
            )
            for g in goals
        }

    return results
