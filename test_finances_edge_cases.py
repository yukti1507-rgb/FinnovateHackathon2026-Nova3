"""Non-happy-path tests for the Your Finances page.

Run with: pytest test_finances_edge_cases.py -v
"""

import uuid

import pytest
from streamlit.testing.v1 import AppTest

from app_model.db import get_connection
from app_model.schema import create_all_tables
from app_model.users import add_user, delete_user, get_user
from registration_and_login.hashing import generate_hash


PAGE = "pages/2_Your_Finances.py"


def button(at, label):
    return next(item for item in at.button if item.label == label)


@pytest.fixture
def test_user():
    username = f"finances_e2e_{uuid.uuid4().hex[:10]}"
    email = f"{username}@example.test"
    conn = get_connection()
    create_all_tables(conn)
    add_user(conn, username, generate_hash("ValidPassword123!"), email)
    user_id = get_user(conn, username)[0]

    yield conn, username, user_id

    delete_user(conn, username)
    conn.close()


def finances_app(test_user, **state):
    conn, username, user_id = test_user
    at = AppTest.from_file(PAGE, default_timeout=10)
    at.session_state["Logged_in"] = True
    at.session_state["username"] = username
    at.session_state["user_id"] = user_id
    for key, value in state.items():
        at.session_state[key] = value
    at.run()
    assert not at.exception
    return at


def test_rejects_zero_main_income_on_save(test_user):
    at = finances_app(test_user, income=0.0)

    at.button(key="save_income_btn").click().run()

    assert not at.exception
    assert at.error
    assert "Main income must be greater than 0." in at.error[-1].value
    assert "show_income_confirmation" not in at.session_state


def test_rejects_blank_and_zero_expense_before_draft_save(test_user):
    at = finances_app(test_user, income=5000.0)

    button(at, "Add expense").click().run()

    assert not at.exception
    assert at.error
    assert "Please enter an expense name." in at.error[-1].value
    assert at.session_state["expense_draft"] == []

    at.text_input(key="new_expense_name").set_value("Rent")
    at.number_input(key="new_expense_amount").set_value(0.0)
    button(at, "Add expense").click().run()

    assert not at.exception
    assert at.error
    assert "Amount must be greater than 0." in at.error[-1].value
    assert at.session_state["expense_draft"] == []


def test_rejects_blank_loan_name_and_zero_payment(test_user):
    at = finances_app(test_user)

    button(at, "Add loan").click().run()

    assert not at.exception
    assert at.error
    assert "Please enter a loan name." in at.error[-1].value
    assert at.session_state["loan_draft"] == []

    at.text_input(key="new_loan_name").set_value("Car")
    at.number_input(key="new_loan_principal").set_value(10000.0)
    at.number_input(key="new_loan_payment").set_value(0.0)
    button(at, "Add loan").click().run()

    assert not at.exception
    assert at.error
    assert "Monthly payment must be greater than 0." in at.error[-1].value
    assert at.session_state["loan_draft"] == []


def test_warns_when_expenses_exceed_income(test_user):
    at = finances_app(
        test_user,
        income=1000.0,
        expense_draft=[
            {
                "id": "new_1",
                "category": "Housing",
                "name": "Rent",
                "amount": 1500.0,
                "currency": "MUR",
                "frequency": "monthly",
                "expense_type": "Need",
            }
        ],
    )

    assert any("expenses currently exceed your income" in item.value for item in at.warning)
    assert at.session_state["expense_draft"][0]["name"] == "Rent"


def test_removing_an_expense_updates_the_unsaved_draft(test_user):
    at = finances_app(
        test_user,
        expense_draft=[
            {
                "id": "new_1",
                "category": "Food",
                "name": "Groceries",
                "amount": 300.0,
                "currency": "MUR",
                "frequency": "weekly",
                "expense_type": "Need",
            }
        ],
    )

    at.button(key="remove_expense_new_1").click().run()

    assert not at.exception
    assert at.session_state["expense_draft"] == []
    assert any("haven't added any expenses yet" in item.value for item in at.info)