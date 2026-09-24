from math import ceil


def resolve_goal_deadline_months(goal, today=None):
    """Return the effective deadline in months for a goal.

    Prefer target_date, and only fall back to legacy years when the
    target date is missing. This keeps the modern deadline model as the
    single source of truth while staying compatible with older data.
    """
    if goal is None:
        return 0

    target_date = goal.get("target_date")
    if target_date is not None:
        return max(int(calculate_months_remaining(target_date, today=today) or 0), 0)

    years = goal.get("years")
    if years is None:
        return 0

    try:
        return max(int(float(years) * 12), 0)
    except (TypeError, ValueError):
        return 0


def calculate_months_remaining(target_date, today=None):
    """
    Calculate the approximate number of whole months remaining
    until a goal's target date.

    target_date can be:
        - a datetime.date
        - a datetime.datetime
        - an ISO date string: YYYY-MM-DD
    """

    from datetime import date, datetime

    if target_date is None:
        return None

    if isinstance(target_date, str):
        target_date = datetime.strptime(
            target_date,
            "%Y-%m-%d"
        ).date()

    if isinstance(target_date, datetime):
        target_date = target_date.date()

    if today is None:
        today = date.today()

    months = (
        (target_date.year - today.year) * 12
        + (target_date.month - today.month)
    )

    # If the target date is later in the current month,
    # still count the current month as available.
    if target_date.day >= today.day:
        months += 1

    return max(months, 0)


def calculate_goal_metrics(
    target_cents,
    current_cents,
    months_remaining
):
    """
    Calculate the basic financial metrics for one goal.

    All monetary calculations use integer cents.
    """

    target_cents = max(int(target_cents), 0)
    current_cents = max(int(current_cents), 0)

    remaining_cents = max(
        target_cents - current_cents,
        0
    )

    if months_remaining is None:
        required_monthly_cents = None

    elif months_remaining <= 0:
        required_monthly_cents = (
            remaining_cents
            if remaining_cents > 0
            else 0
        )

    else:
        required_monthly_cents = (
            remaining_cents + months_remaining - 1
        ) // months_remaining

    if target_cents > 0:
        progress_percent = (
            current_cents * 100
        ) // target_cents

        progress_percent = min(
            progress_percent,
            100
        )
    else:
        progress_percent = 100

    return {
        "target_cents": target_cents,
        "current_cents": current_cents,
        "remaining_cents": remaining_cents,
        "required_monthly_cents": required_monthly_cents,
        "progress_percent": progress_percent,
    }


def calculate_goal_urgency(
    months_remaining,
    priority=0
):
    """
    Calculate a deterministic urgency score.

    This is NOT an AI decision.
    It is simply a numerical input that can be used
    by the allocation engine.

    Higher score = greater urgency.
    """

    priority = max(int(priority), 0)

    if months_remaining is None:
        deadline_score = 0

    elif months_remaining <= 1:
        deadline_score = 100

    elif months_remaining <= 3:
        deadline_score = 90

    elif months_remaining <= 6:
        deadline_score = 75

    elif months_remaining <= 12:
        deadline_score = 55

    elif months_remaining <= 24:
        deadline_score = 35

    else:
        deadline_score = 15

    priority_score = min(priority * 10, 30)

    return deadline_score + priority_score


def calculate_goal_allocation(
    goals,
    total_current_savings_cents,
    monthly_savings_cents
):
    """
    Generate a suggested allocation across goals.

    The allocation considers:
        - target amount
        - current amount
        - deadline
        - user priority
        - amount still required

    All monetary values are integer cents.

    Expected goal structure:

        {
            "id": 1,
            "goal_name": "Emergency Fund",
            "target_cents": 3000000,
            "current_cents": 500000,
            "months_remaining": 4,
            "priority": 3
        }

    Returns a list containing calculated metrics
    and suggested allocations.

    IMPORTANT:
    This is a deterministic Python calculation.
    AI is not required.
    """

    total_current_savings_cents = max(
        int(total_current_savings_cents),
        0
    )

    monthly_savings_cents = max(
        int(monthly_savings_cents),
        0
    )

    if not goals:
        return []

    calculated_goals = []

    for goal in goals:
        target_cents = max(
            int(goal.get("target_cents", 0)),
            0
        )

        current_cents = max(
            int(goal.get("current_cents", 0)),
            0
        )

        months_remaining = goal.get(
            "months_remaining"
        )

        priority = goal.get(
            "priority",
            0
        )

        metrics = calculate_goal_metrics(
            target_cents,
            current_cents,
            months_remaining
        )

        urgency_score = calculate_goal_urgency(
            months_remaining,
            priority
        )

        calculated_goals.append({
            **goal,
            **metrics,
            "urgency_score": urgency_score
        })

    # --------------------------------------------------
    # CURRENT SAVINGS ALLOCATION
    # --------------------------------------------------

    # Current savings are distributed according to
    # remaining need weighted by urgency.
    #
    # This means a goal that is both urgent and has
    # substantial remaining need receives more of the
    # suggested current-savings allocation.
    # --------------------------------------------------

    current_weights = []

    for goal in calculated_goals:
        weight = (
            goal["remaining_cents"]
            * max(goal["urgency_score"], 1)
        )

        current_weights.append(weight)

    total_current_weight = sum(
        current_weights
    )

    if total_current_weight == 0:
        current_allocations = [
            0 for _ in calculated_goals
        ]
    else:
        current_allocations = [
            (
                total_current_savings_cents
                * weight
            ) // total_current_weight
            for weight in current_weights
        ]

    # Correct integer rounding so the allocations
    # always add up exactly to the available savings.
    current_difference = (
        total_current_savings_cents
        - sum(current_allocations)
    )

    if current_allocations:
        current_allocations[0] += current_difference

    # --------------------------------------------------
    # MONTHLY SAVINGS ALLOCATION
    # --------------------------------------------------

    monthly_weights = []

    for goal in calculated_goals:

        required = goal[
            "required_monthly_cents"
        ]

        if required is None:
            required = 0

        # Goals that need more per month receive
        # greater weight, while urgency increases
        # their allocation further.
        weight = (
            required
            * max(goal["urgency_score"], 1)
        )

        monthly_weights.append(weight)

    total_monthly_weight = sum(
        monthly_weights
    )

    if total_monthly_weight == 0:
        monthly_allocations = [
            0 for _ in calculated_goals
        ]
    else:
        monthly_allocations = [
            (
                monthly_savings_cents
                * weight
            ) // total_monthly_weight
            for weight in monthly_weights
        ]

    monthly_difference = (
        monthly_savings_cents
        - sum(monthly_allocations)
    )

    if monthly_allocations:
        monthly_allocations[0] += monthly_difference

    # --------------------------------------------------
    # FINAL RESULTS
    # --------------------------------------------------

    results = []

    for index, goal in enumerate(calculated_goals):

        allocated_current = (
            current_allocations[index]
        )

        allocated_monthly = (
            monthly_allocations[index]
        )

        remaining_after_current = max(
            goal["target_cents"]
            - allocated_current,
            0
        )

        required_monthly = goal[
            "required_monthly_cents"
        ]

        if required_monthly is None:
            monthly_shortfall = None

        else:
            monthly_shortfall = max(
                required_monthly
                - allocated_monthly,
                0
            )

        results.append({
            **goal,

            "suggested_current_allocation_cents":
                allocated_current,

            "suggested_monthly_allocation_cents":
                allocated_monthly,

            "remaining_after_current_cents":
                remaining_after_current,

            "monthly_shortfall_cents":
                monthly_shortfall,

            "is_on_track":
                (
                    monthly_shortfall is not None
                    and monthly_shortfall == 0
                )
        })

    return results


def calculate_projected_completion(
    current_cents,
    target_cents,
    monthly_allocation_cents
):
    """
    Calculate the number of months needed to reach
    a goal using a fixed monthly allocation.

    This function deliberately ignores investment returns
    for now. Interest/growth can be incorporated later
    without changing the allocation interface.
    """

    current_cents = max(
        int(current_cents),
        0
    )

    target_cents = max(
        int(target_cents),
        0
    )

    monthly_allocation_cents = max(
        int(monthly_allocation_cents),
        0
    )

    remaining_cents = max(
        target_cents - current_cents,
        0
    )

    if remaining_cents == 0:
        return 0

    if monthly_allocation_cents <= 0:
        return None

    return (
        remaining_cents
        + monthly_allocation_cents
        - 1
    ) // monthly_allocation_cents


def calculate_what_if(
    goals,
    allocations_cents
):
    """
    Recalculate goal progress using a user-defined
    monthly allocation.

    `allocations_cents` should be a dictionary:

        {
            goal_id: monthly_amount_cents
        }

    This uses the same mathematical logic as the
    normal allocation system.

    It does NOT call AI.
    """

    results = []

    for goal in goals:

        goal_id = goal["id"]

        current_cents = max(
            int(goal.get("current_cents", 0)),
            0
        )

        target_cents = max(
            int(goal.get("target_cents", 0)),
            0
        )

        monthly_allocation = max(
            int(
                allocations_cents.get(
                    goal_id,
                    0
                )
            ),
            0
        )

        remaining_cents = max(
            target_cents - current_cents,
            0
        )

        months = calculate_projected_completion(
            current_cents,
            target_cents,
            monthly_allocation
        )

        results.append({
            **goal,

            "monthly_allocation_cents":
                monthly_allocation,

            "remaining_cents":
                remaining_cents,

            "projected_completion_months":
                months
        })

    return results