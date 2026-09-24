"""Happy- and unhappy-path smoke tests for every application page.

Run with: pytest test_all_pages_paths.py -v
"""

import uuid

import pytest
from streamlit.testing.v1 import AppTest

from app_model.db import get_connection
from app_model.schema import create_all_tables
from app_model.users import add_user, delete_user, get_user
from registration_and_login.hashing import generate_hash


def base_state():
    return {
        "income": 50000.0,
        "expenses": 30000.0,
        "current_savings": 20000.0,
        "monthly_savings": 10000.0,
        "savings_rate": 3.0,
        "goals": [{"name": "Laptop", "amount": 45000.0, "years": 1}],
        "loans": [{"name": "Car", "principal": 50000.0, "rate": 9.0, "payment": 2000.0}],
        "expense_categories": [{"name": "Rent", "amount": 30000.0, "type": "Need"}],
        "language": "en",
        "existing_loan_payment": 2000.0,
        "loan2_debt": 2000.0,
    }


def run_page(path, state=None):
    at = AppTest.from_file(path, default_timeout=30)
    for key, value in (state or {}).items():
        at.session_state[key] = value
    at.run()
    return at


@pytest.fixture
def application_user():
    username = f"page_e2e_{uuid.uuid4().hex[:10]}"
    conn = get_connection()
    create_all_tables(conn)
    add_user(conn, username, generate_hash("ValidPassword123!"), f"{username}@example.test")
    user_id = get_user(conn, username)[0]

    yield conn, username, user_id

    delete_user(conn, username)
    conn.close()


def logged_in_state(application_user, **extra):
    _, username, user_id = application_user
    state = base_state()
    state.update({"Logged_in": True, "username": username, "user_id": user_id})
    state.update(extra)
    return state


def test_profile_happy_path_renders(application_user):
    at = run_page("pages/1_Profile.py", logged_in_state(application_user))
    assert not at.exception
    assert any("Profile page" in item.value for item in at.markdown)


def test_profile_unhappy_path_requires_login():
    at = run_page("pages/1_Profile.py")
    assert not at.exception
    assert any("Please log in" in item.value for item in at.warning)


def test_finances_happy_path_renders_for_logged_in_user(application_user):
    at = run_page("pages/2_Your_Finances.py", logged_in_state(application_user))
    assert not at.exception
    assert any("Monthly income overview" in item.value for item in at.markdown)


def test_finances_unhappy_path_requires_login():
    at = run_page("pages/2_Your_Finances.py")
    assert not at.exception
    assert any("Please log in" in item.value for item in at.error)


def test_dashboard_happy_path_shows_goal_verdict():
    at = run_page("pages/3_Dashboard.py", base_state())
    assert not at.exception
    assert at.success or at.warning or at.error


def test_dashboard_unhappy_path_requests_finance_details():
    at = run_page("pages/3_Dashboard.py")
    assert not at.exception
    assert any("fill in your details first" in item.value for item in at.warning)


def test_loans_happy_path_renders_repayment_plan():
    at = run_page("pages/4_Loans.py", base_state())
    assert not at.exception
    assert any("need to pay" in item.value for item in at.info)


def test_loans_unhappy_path_handles_missing_loan_and_income():
    at = run_page("pages/4_Loans.py", {"income": 0.0, "expenses": 0.0, "loans": []})
    assert not at.exception
    assert any("haven't added any loans" in item.value for item in at.info)

    at.button[-1].click().run()
    assert not at.exception
    assert any("fill in your income" in item.value for item in at.error)


def test_admin_happy_path_renders_for_admin(application_user):
    at = run_page(
        "pages/5_Admin.py",
        {"Admin": True, "Logged_in": True, "username": application_user[1]},
    )
    assert not at.exception
    assert any("Admin Dashboard" in item.value for item in at.title)


def test_admin_unhappy_path_denies_non_admin_access():
    at = run_page("pages/5_Admin.py", {"Admin": False})
    assert not at.exception
    assert any("Access denied" in item.value for item in at.error)


def test_finance_profile_happy_path_renders_snapshot():
    at = run_page("pages/6_Finance_Profile.py", base_state())
    assert not at.exception
    assert any("Your Finance Profile" in item.value for item in at.title)


def test_finance_profile_unhappy_path_requests_finance_details():
    at = run_page("pages/6_Finance_Profile.py")
    assert not at.exception
    assert any("fill in your details first" in item.value for item in at.warning)