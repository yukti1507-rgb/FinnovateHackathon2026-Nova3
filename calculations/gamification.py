from pathlib import Path


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


MILESTONES = (0, 20, 40, 60, 80, 100)


def get_current_milestone(current_savings, target_amount):
    """Return the highest milestone reached for a goal."""
    progress = calculate_goal_progress(current_savings, target_amount)
    return max(
        milestone
        for milestone in MILESTONES
        if progress >= milestone
    )


def get_next_milestone(current_savings, target_amount):
    """Return the next milestone, or 100 when the goal is complete."""
    current_milestone = get_current_milestone(
        current_savings,
        target_amount
    )

    for milestone in MILESTONES:
        if milestone > current_milestone:
            return milestone

    return 100


def check_for_new_milestone(previous_milestone, current_milestone):
    """Return a newly reached milestone, if one exists."""
    if current_milestone > previous_milestone:
        return current_milestone

    return None


def get_milestone_message(milestone):
    """Return the existing dashboard message for a milestone."""
    if milestone >= 100:
        return "Congratulations! You reached your goal."

    return f"You reached the {milestone}% milestone. Keep going!"


def get_stage_image(stage, theme="house"):
    """Return the shared progress image used by the dashboard."""
    return str(
        Path(__file__).resolve().parent.parent
        / "assets"
        / "image.png"
    )