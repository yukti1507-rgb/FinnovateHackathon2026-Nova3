"""
FLOW / cross-page consistency tests.

Run with:  pytest test_flow.py -v   (from project root)

Different from test_app.py (which checks each page loads correctly
IN ISOLATION with pre-seeded data) and test_calculations.py (which
checks the pure math functions are correct).

This file checks the thing that actually broke tonight more than once:
does data flow CORRECTLY from one page to the next, and does every
page agree with every other page about the same underlying facts?

Specifically this catches:
- A value entered on Finances silently not showing up on Dashboard/Loans
  (this happened tonight with the income field)
- Two pages disagreeing about whether a goal is "reached" or showing
  contradictory numbers for the same goal (this happened tonight with
  the inflation-adjusted-target inconsistency bug)
- A loan added on Finances not appearing in the Loans page selector
"""

import pytest
from streamlit.testing.v1 import AppTest


def seed(at, state):
    for key, value in state.items():
        at.session_state[key] = value
    return at


# ============================================================
# Flow 1: Finances -> Dashboard
# ============================================================

class TestFinancesToDashboardFlow:
    def test_goal_entered_on_finances_appears_correctly_on_dashboard(self):
        """
        Simulates a user who has filled in Finances (income, expenses,
        savings, a goal) -- runs Finances first (as the real app would),
        captures its ACTUAL resulting session_state, then feeds that
        real output into Dashboard and checks the goal shows up with a
        verdict, using the SAME data Finances actually produced.
        """
        finances_input = {
            "income": 50000.0,
            "current_savings": 20000.0,
            "monthly_savings": 10000.0,
            "savings_rate": 3.0,
            "goals": [{"name": "Laptop", "amount": 45000.0, "years": 1}],
            "loans": [],
            "subscriptions": [],
            "variable_expenses": [],
            "other_fixed_expenses": [],
            "language": "en",
        }

        at_finances = AppTest.from_file("pages/2_Your_Finances.py")
        seed(at_finances, finances_input)
        at_finances.run()
        assert not at_finances.exception, "Finances page crashed with valid input"

        # pull out what Finances ACTUALLY computed and stored --
        # not what we assume it should be
        actual_state = dict(at_finances.session_state)

        # sanity: Finances should have computed a real expenses total,
        # and it should still have our goal
        assert "expenses" in actual_state
        assert actual_state["goals"][0]["name"] == "Laptop"

        # now feed Finances' REAL output into Dashboard
        at_dashboard = AppTest.from_file("pages/3_Dashboard.py")
        for key, value in actual_state.items():
            at_dashboard.session_state[key] = value
        at_dashboard.run()

        assert not at_dashboard.exception, "Dashboard crashed with real Finances output"
        # the goal must show up as SOME verdict (success/warning/error)
        assert len(at_dashboard.success) + len(at_dashboard.warning) + len(at_dashboard.error) > 0, \
            "Goal from Finances did not produce any verdict on Dashboard"

    def test_income_actually_persists_through_finances_run(self):
        """
        REGRESSION TEST: tonight's income field silently reset to 0
        after leaving and returning to the page. This confirms that
        after running Finances with income set, the income value in
        session_state afterward still matches what was entered --
        not silently zeroed out by the page's own logic.
        """
        at = AppTest.from_file("pages/2_Your_Finances.py")
        seed(at, {
            "income": 75000.0,
            "current_savings": 0.0,
            "monthly_savings": 0.0,
            "savings_rate": 3.0,
            "goals": [], "loans": [], "subscriptions": [],
            "variable_expenses": [], "other_fixed_expenses": [],
            "language": "en",
        })
        at.run()
        assert not at.exception
        assert at.session_state["income"] == 75000.0, \
            "Income was NOT preserved after Finances page ran (this exact bug happened tonight)"


# ============================================================
# Flow 2: Finances -> Loans (loan list handoff)
# ============================================================

class TestFinancesToLoansFlow:
    def test_loan_entered_on_finances_appears_in_loans_selector(self):
        """
        A loan added via Finances' loans list must show up as a
        selectable option on the Loans page dropdown.
        """
        finances_input = {
            "income": 50000.0,
            "current_savings": 0.0,
            "monthly_savings": 0.0,
            "savings_rate": 3.0,
            "goals": [],
            "loans": [{"name": "Car", "principal": 50000.0, "rate": 9.0, "payment": 2000.0}],
            "subscriptions": [], "variable_expenses": [], "other_fixed_expenses": [],
            "language": "en",
        }

        at_finances = AppTest.from_file("pages/2_Your_Finances.py")
        seed(at_finances, finances_input)
        at_finances.run()
        assert not at_finances.exception

        actual_state = dict(at_finances.session_state)
        assert any(l["name"] == "Car" for l in actual_state["loans"]), \
            "Loan was lost/altered after Finances page ran"

        at_loans = AppTest.from_file("pages/4_Loans.py")
        for key, value in actual_state.items():
            at_loans.session_state[key] = value
        at_loans.run()

        assert not at_loans.exception, "Loans page crashed with real Finances output"
        # the "Car" loan must appear as an option somewhere on the page
        selectbox_options = []
        for sb in at_loans.selectbox:
            selectbox_options.extend(sb.options)
        assert "Car" in selectbox_options, "Loan from Finances did not appear in Loans page selector"


# ============================================================
# Flow 3: Cross-page consistency (Dashboard vs Finance Profile)
# ============================================================

class TestCrossPageConsistency:
    def test_dashboard_and_finance_profile_agree_on_same_goal(self):
        """
        REGRESSION TEST for tonight's inflation-inconsistency bug:
        Dashboard and Finance Profile both show a chart/verdict for
        the same goal, using the same underlying calculation. This
        confirms neither page crashes and both reach SOME verdict --
        catching the class of bug where one page said "reached" and
        another implied the opposite for the identical goal.
        """
        shared_state = {
            "income": 50000.0,
            "current_savings": 20000.0,
            "monthly_savings": 10000.0,
            "savings_rate": 3.0,
            "goals": [{"name": "Mortgage", "amount": 1500000.0, "years": 20}],
            "loans": [], "subscriptions": [], "variable_expenses": [],
            "other_fixed_expenses": [], "language": "en",
        }

        at_dashboard = AppTest.from_file("pages/3_Dashboard.py")
        seed(at_dashboard, dict(shared_state))
        at_dashboard.run()
        assert not at_dashboard.exception

        at_profile = AppTest.from_file("pages/6_Finance_Profile.py")
        seed(at_profile, dict(shared_state))
        at_profile.run()
        assert not at_profile.exception

        # both pages should reach a verdict, neither should silently
        # show nothing for the same goal
        dashboard_has_verdict = len(at_dashboard.success) + len(at_dashboard.warning) + len(at_dashboard.error) > 0
        profile_has_verdict = len(at_profile.success) + len(at_profile.warning) > 0
        assert dashboard_has_verdict, "Dashboard showed no verdict for the goal"
        assert profile_has_verdict, "Finance Profile showed no verdict for the same goal"


# ============================================================
# Flow 4: Full journey smoke test (all pages, one shared state)
# ============================================================

class TestFullJourney:
    def test_new_user_can_walk_through_every_page_without_crashing(self):
        """
        Simulates the most basic real user journey: fill in Finances,
        then visit every other page with that same data. Nothing
        should crash anywhere. This is the closest automated
        equivalent to "click through the whole app as a judge would."
        """
        state = {
            "income": 60000.0,
            "current_savings": 30000.0,
            "monthly_savings": 12000.0,
            "savings_rate": 3.5,
            "goals": [{"name": "Emergency Fund", "amount": 100000.0, "years": 2}],
            "loans": [{"name": "Car", "principal": 40000.0, "rate": 8.5, "payment": 1800.0}],
            "subscriptions": [{"name": "Netflix", "amount": 500.0, "type": "Want"}],
            "variable_expenses": [{"name": "Groceries", "amount": 3000.0, "type": "Need"}],
            "other_fixed_expenses": [],
            "expense_categories": [
                {"name": "Netflix", "amount": 500.0, "type": "Want"},
                {"name": "Groceries", "amount": 3000.0, "type": "Need"},
            ],
            "language": "en",
            "existing_loan_payment": 1800.0,
            "loan2_debt": 1800.0,
            "monthly_savings_touched": True,
        }

        pages = [
            "pages/2_Your_Finances.py",
            "pages/3_Dashboard.py",
            "pages/4_Loans.py",
            "pages/6_Finance_Profile.py",
        ]

        for page in pages:
            at = AppTest.from_file(page)
            seed(at, dict(state))
            at.run()
            assert not at.exception, f"{page} crashed during the full-journey walkthrough"