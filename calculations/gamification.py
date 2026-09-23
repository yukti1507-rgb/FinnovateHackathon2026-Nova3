def calculate_goal_progress(current_savings, target_amount):
    """
    Calculate progress toward a financial goal as a percentage.
    Progress is capped between 0% and 100%.
    """
    if target_amount <= 0:
        return 100.0

    progress = (current_savings / target_amount) * 100

    return min(max(progress, 0), 100)


def get_goal_stage(current_savings, target_amount):
    """
    Divide goal progress into 6 stages.

    0 = 0–19%
    1 = 20–39%
    2 = 40–59%
    3 = 60–79%
    4 = 80–99%
    5 = 100%
    """
    progress = calculate_goal_progress(current_savings, target_amount)

    if progress >= 100:
        return 5
    elif progress >= 80:
        return 4
    elif progress >= 60:
        return 3
    elif progress >= 40:
        return 2
    elif progress >= 20:
        return 1
    else:
        return 0


def get_stage_name(stage):
    """
    Return a simple name for each progress stage.
    """
    stages = {
        0: "Getting Started",
        1: "First Steps",
        2: "Taking Shape",
        3: "Growing",
        4: "Almost There",
        5: "Goal Reached"
    }

    return stages.get(stage, "Getting Started")