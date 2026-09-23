"""
Automated UI/integration tests using Streamlit's AppTest framework.

Run with:  pytest test_app.py -v

Run this from your PROJECT ROOT (same folder as Home.py) so the
relative paths to pages/ resolve correctly.

These tests load your actual page scripts with realistic pre-filled
session_state (simulating a user who already filled in Finances) and
check that each page renders WITHOUT crashing. They deliberately do
NOT click the AI explanation buttons (Explain my results, How can I
close this gap, etc.) since those make real calls to the Groq API --
slow, costs your quota, and the AI's exact wording isn't something you
can strictly pass/fail test anyway. Your calculation logic is already
covered separately by test_calculations.py (pytest, pure functions).

This file focuses on the thing test_calculations.py CAN'T check:
does the actual Streamlit page render correctly with real data,
without throwing an exception.
"""

import pytest
from streamlit.testing.v1 import AppTest


def make_realistic_state(goal_years=1, goal_amount=45000.0):
    """
    A realistic, fully-filled-in session_state, as if the user had
    already completed the Finances page. Used to pre-seed every test
    below so each page loads as it would for a real user, not an
    empty first-time visitor.
    """
    return {
        "income": 50000.0,
        "expenses": 30000.0,
        "current_savings": 20000.0,
        "monthly_savings": 10000.0,
        "savings_rate": 3.0,
        "goals": [{"name": "Laptop", "amount": goal_amount, "years": goal_years}],
        "loans": [{"name": "Car", "principal": 50000.0, "rate": 9.0, "payment": 2000.0}],
        "subscriptions": [{"name": "Netflix", "amount": 500.0, "type": "Want"}],
        "variable_expenses": [{"name": "Market", "amount": 2000.0, "type": "Need"}],
        "other_fixed_expenses": [],
        "expense_categories": [
            {"name": "Rent/Mortgage", "amount": 15000.0, "type": "Need"},
            {"name": "Netflix", "amount": 500.0, "type": "Want"},
            {"name": "Market", "amount": 2000.0, "type": "Need"},
        ],
        "language": "en",
        "existing_loan_payment": 2000.0,
        "loan2_debt": 2000.0,
        "monthly_savings_touched": True,
    }


def seed(at, state):
    """Helper: push every key/value in `state` into the AppTest's session_state."""
    for key, value in state.items():
        at.session_state[key] = value
    return at


# ============================================================
# Finances page
# ============================================================

class TestFinancesPage:
    def test_loads_without_error_on_first_visit(self):
        """A brand new user with nothing filled in yet -- should not crash."""
        at = AppTest.from_file("pages/2_Your_Finances.py")
        at.run()
        assert not at.exception

    def test_loads_without_error_with_full_data(self):
        """A returning user with everything filled in -- should not crash."""
        at = AppTest.from_file("pages/2_Your_Finances.py")
        seed(at, make_realistic_state())
        at.run()
        assert not at.exception

    def test_survives_language_switch_to_french(self):
        at = AppTest.from_file("pages/2_Your_Finances.py")
        state = make_realistic_state()
        state["language"] = "fr"
        seed(at, state)
        at.run(timeout=30)  # translation makes real API calls -- needs more time
        assert not at.exception


# ============================================================
# Dashboard page
# ============================================================

class TestDashboardPage:
    def test_shows_warning_when_no_income_set(self):
        """No data yet -- should show a warning, not crash."""
        at = AppTest.from_file("pages/3_Dashboard.py")
        at.run()
        assert not at.exception
        assert len(at.warning) > 0

    def test_loads_without_error_with_a_normal_goal(self):
        at = AppTest.from_file("pages/3_Dashboard.py")
        seed(at, make_realistic_state())
        at.run()
        assert not at.exception
        # some verdict (success/warning/error) should be shown for the goal
        assert len(at.success) + len(at.warning) + len(at.error) > 0

    def test_regression_long_deadline_goal_does_not_crash_chart(self):
        """
        REGRESSION TEST: this is the exact bug your teammate found --
        a long-deadline goal (e.g. 20-year mortgage payoff) used to
        corrupt the inflation-vs-savings chart because two lists of
        different lengths were compared. This confirms it's fixed.
        """
        at = AppTest.from_file("pages/3_Dashboard.py")
        state = make_realistic_state(goal_years=20, goal_amount=1500000.0)
        seed(at, state)
        at.run()
        assert not at.exception

    def test_short_goal_still_works(self):
        """Sanity check the opposite extreme -- a 1-year goal."""
        at = AppTest.from_file("pages/3_Dashboard.py")
        state = make_realistic_state(goal_years=1, goal_amount=10000.0)
        seed(at, state)
        at.run()
        assert not at.exception

    def test_survives_language_switch_to_french(self):
        at = AppTest.from_file("pages/3_Dashboard.py")
        state = make_realistic_state()
        state["language"] = "fr"
        seed(at, state)
        at.run(timeout=30)  # translation makes real API calls -- needs more time
        assert not at.exception


# ============================================================
# Loans page
# ============================================================

class TestLoansPage:
    def test_shows_info_when_no_loans_added(self):
        at = AppTest.from_file("pages/4_Loans.py")
        at.session_state["loans"] = []
        at.session_state["income"] = 0.0
        at.session_state["expenses"] = 0.0
        at.run()
        assert not at.exception

    def test_loads_without_error_with_a_loan(self):
        at = AppTest.from_file("pages/4_Loans.py")
        seed(at, make_realistic_state())
        at.run()
        assert not at.exception

    def test_loads_with_multiple_loans(self):
        """Confirms the loan selector dropdown handles more than one loan."""
        at = AppTest.from_file("pages/4_Loans.py")
        state = make_realistic_state()
        state["loans"] = [
            {"name": "Car", "principal": 50000.0, "rate": 9.0, "payment": 2000.0},
            {"name": "House", "principal": 2000000.0, "rate": 7.5, "payment": 15000.0},
        ]
        seed(at, state)
        at.run()
        assert not at.exception

    def test_survives_language_switch_to_french(self):
        at = AppTest.from_file("pages/4_Loans.py")
        state = make_realistic_state()
        state["language"] = "fr"
        seed(at, state)
        at.run(timeout=30)  # translation makes real API calls -- needs more time
        assert not at.exception


# ============================================================
# Finance Profile page
# ============================================================

class TestFinanceProfilePage:
    def test_loads_without_error_with_full_data(self):
        at = AppTest.from_file("pages/6_Finance_Profile.py")
        seed(at, make_realistic_state())
        at.run()
        assert not at.exception

    def test_loads_without_error_with_long_goal(self):
        """Same regression check as Dashboard, for this page's own goal chart."""
        at = AppTest.from_file("pages/6_Finance_Profile.py")
        state = make_realistic_state(goal_years=20, goal_amount=1500000.0)
        seed(at, state)
        at.run()
        assert not at.exception

    def test_loads_without_error_with_no_data(self):
        at = AppTest.from_file("pages/6_Finance_Profile.py")
        at.run()
        assert not at.exception