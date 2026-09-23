from calculations.savings import project_savings
from calculations.loans import amortisation_schedule, calculate_monthly_payment
from calculations.goals import required_monthly_contribution, check_all_goals, months_to_reach_at_current_rate, inflation_adjusted_target


def run_full_simulation(user_data, months=60):
    """
    Takes the dictionary of user inputs (from session_state) and
    returns a full results package: savings projection, loan schedule
    (if applicable), and goal progress (if applicable).
    """
    results = {}

    # Always run savings projection
    results["savings_projection"] = project_savings(
        starting_balance=user_data["current_savings"],
        monthly_contribution=user_data["monthly_savings"],
        annual_rate=user_data["savings_rate"],
        months=months
    )

    # Only run loan calculations if the user has a loan
    if user_data.get("has_loan"):
        monthly_payment = calculate_monthly_payment(
            principal=user_data["loan_amount"],
            annual_rate=user_data["loan_rate"],
            term_years=user_data["loan_term_years"]
        )
        results["loan_schedule"] = amortisation_schedule(
            principal=user_data["loan_amount"],
            annual_rate=user_data["loan_rate"],
            monthly_payment=monthly_payment,
            term_months=user_data["loan_term_years"] * 12
        )


    # Only run goal calculations if the user has a goal
    if user_data.get("goals"):
        results["goals_status"] = check_all_goals(
            results["savings_projection"], user_data["goals"]
        )

        #what each goal will actually cost by its deadline, with inflation
        #IMPORTANT: computed FIRST, so every other calc below uses this
        #SAME real (inflation-adjusted) target -- never the raw today-price
        #amount. Mixing raw and inflated targets across calculations was
        #causing contradictory messages (e.g. "you'll reach it sooner"
        #alongside "that's later than your target").
        results["inflation_adjusted_target_per_goal"] = {
            g["name"]: inflation_adjusted_target(g["amount"], g["years"])
            for g in user_data["goals"]
        }

        results["required_monthly_per_goal"] = {
            g["name"]: required_monthly_contribution(
                results["inflation_adjusted_target_per_goal"][g["name"]],
                user_data["current_savings"],
                user_data["savings_rate"], g["years"] * 12
            )
            for g in user_data["goals"]
        }

        #actual time to reach each goal's REAL (inflated) target at
        #current rate, no deadline
        results["actual_months_per_goal"] = {
            g["name"]: months_to_reach_at_current_rate(
                user_data["current_savings"], user_data["monthly_savings"],
                user_data["savings_rate"],
                results["inflation_adjusted_target_per_goal"][g["name"]]
            )
            for g in user_data["goals"]
        }

    return results