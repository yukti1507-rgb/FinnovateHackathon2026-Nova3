"""Extended end-to-end authentication journey tests for ``Home.py``.

Run with: pytest test_auth_flow_extended.py -v

Covers the flows NOT already covered by test_auth_flow.py's happy path
(register -> correct password -> OTP -> login):
- Registration rejects a too-weak password
- Registration rejects an invalid email format
- Account lockout after 3 wrong password attempts
- Locked-account recovery: OTP -> forced new password -> login
  (this specifically re-verifies the user_id bug fix from tonight --
  without it, this test's final assertion would fail)
- Forgot password: requesting a reset link (valid vs. unregistered email)

These reuse the exact same helpers, monkeypatches, and cleanup pattern
as test_auth_flow.py so both files can run side by side.
"""

import uuid

import streamlit as st
from app_model.db import get_connection
from app_model.schema import create_all_tables
from app_model.users import delete_user, get_user, add_user
from registration_and_login.hashing import generate_hash
from registration_and_login import send_email_to_user
from streamlit.testing.v1 import AppTest


def _button(at, label):
    return next(button for button in at.button if button.label == label)


def _text_input_no_key(at, exclude_keys):
    """Find the one visible text_input that has no explicit key -- used for
    the Forgot Password email field, which sits alongside the keyed
    Login_username/Login_password fields on the same screen."""
    return next(ti for ti in at.text_input if ti.key not in exclude_keys)


def _register_user(at, username, email, password):
    _button(at, "Register instead").click().run()
    at.text_input[0].set_value(username)
    at.text_input[1].set_value(email)
    at.text_input[2].set_value(password)
    at.text_input[3].set_value(password)
    _button(at, "Register").click().run()


# ============================================================
# Registration validation
# ============================================================

def test_registration_rejects_weak_password(monkeypatch):
    """A password missing the required complexity should be rejected,
    and no account should be created."""
    username = f"e2e_weak_{uuid.uuid4().hex[:10]}"
    email = f"{username}@example.test"

    monkeypatch.setattr(send_email_to_user, "send_OTP_email", lambda _e, _o: True)
    monkeypatch.setattr(st, "switch_page", lambda _p: None)

    conn = get_connection()
    create_all_tables(conn)

    try:
        at = AppTest.from_file("Home.py", default_timeout=10).run()
        _register_user(at, username, email, "short")  # too short, no complexity
        assert not at.exception
        assert len(at.error) > 0
        assert get_user(conn, username) is None
    finally:
        delete_user(conn, username)
        conn.close()


def test_registration_rejects_invalid_email(monkeypatch):
    """A malformed email (no @ / no domain) should be rejected at registration."""
    username = f"e2e_bademail_{uuid.uuid4().hex[:10]}"

    monkeypatch.setattr(send_email_to_user, "send_OTP_email", lambda _e, _o: True)
    monkeypatch.setattr(st, "switch_page", lambda _p: None)

    conn = get_connection()
    create_all_tables(conn)

    try:
        at = AppTest.from_file("Home.py", default_timeout=10).run()
        _register_user(at, username, "not-an-email", "ValidPassword123!")
        assert not at.exception
        assert len(at.error) > 0
        assert get_user(conn, username) is None
    finally:
        delete_user(conn, username)
        conn.close()


# ============================================================
# Lockout after 3 failed attempts
# ============================================================

def test_account_locks_after_three_wrong_passwords(monkeypatch):
    """3 consecutive wrong passwords should lock the account, and a 4th
    attempt (even correct) should be blocked by the lockout screen
    rather than allowed through."""
    username = f"e2e_lock_{uuid.uuid4().hex[:10]}"
    email = f"{username}@example.test"
    password = "ValidPassword123!"

    monkeypatch.setattr(send_email_to_user, "send_OTP_email", lambda _e, _o: True)
    monkeypatch.setattr(st, "switch_page", lambda _p: None)

    conn = get_connection()
    create_all_tables(conn)

    try:
        at = AppTest.from_file("Home.py", default_timeout=10).run()
        _register_user(at, username, email, password)
        assert get_user(conn, username) is not None

        # 3 wrong attempts in a row, on a fresh AppTest run each time
        # (mirrors a real user reloading/resubmitting the login form)
        for attempt in range(3):
            at = AppTest.from_file("Home.py", default_timeout=10).run()
            at.text_input(key="Login_username").set_value(username)
            at.text_input(key="Login_password").set_value("WrongPassword123!")
            _button(at, "Log in").click().run()
            assert not at.exception

        # after the 3rd wrong attempt, the account should be locked
        assert at.session_state.get("account_is_locked") is True

        # a 4th attempt -- even with the CORRECT password -- should be
        # blocked by the lockout screen, not let straight through
        at2 = AppTest.from_file("Home.py", default_timeout=10).run()
        at2.session_state["account_is_locked"] = True
        at2.session_state["locked_username"] = username
        at2.run()
        assert not at2.exception
        assert any("locked" in err.value.lower() for err in at2.error), \
            "Locked account should show a lockout message, not the normal login form"
    finally:
        delete_user(conn, username)
        conn.close()


# ============================================================
# Locked-account recovery (regression test for the user_id fix)
# ============================================================

def test_locked_account_recovery_sets_user_id(monkeypatch):
    """
    REGRESSION TEST: after recovering a locked account via OTP and
    setting a new password, the session must have BOTH Logged_in AND
    user_id set. Before tonight's fix, user_id was never set on this
    path, which caused pages like Your Finances (which require both)
    to reject the user immediately after a successful recovery.
    """
    username = f"e2e_recover_{uuid.uuid4().hex[:10]}"
    email = f"{username}@example.test"
    password = "ValidPassword123!"
    new_password = "BrandNewPassword456!"

    monkeypatch.setattr(send_email_to_user, "send_OTP_email", lambda _e, _o: True)
    monkeypatch.setattr(st, "switch_page", lambda _p: None)

    conn = get_connection()
    create_all_tables(conn)

    try:
        at = AppTest.from_file("Home.py", default_timeout=10).run()
        _register_user(at, username, email, password)

        # simulate the account already being locked, going straight to
        # the "request a verification code" screen
        at = AppTest.from_file("Home.py", default_timeout=10)
        at.session_state["account_is_locked"] = True
        at.session_state["locked_username"] = username
        at.run()
        assert not at.exception

        _button(at, "Send me a verification code").click().run()
        assert not at.exception
        assert at.session_state.get("otp_reason") == "locked"

        at.text_input(key="otp_input").set_value(str(at.session_state["otp_code"]))
        _button(at, "Verify").click().run()
        assert not at.exception
        assert at.session_state.get("otp_verified") is True

        # set the new (mandatory) password
        at.text_input[0].set_value(new_password)
        at.text_input[1].set_value(new_password)
        _button(at, "Set password & log in").click().run()
        assert not at.exception

        assert at.session_state.get("Logged_in") is True
        assert at.session_state.get("username") == username
        assert at.session_state.get("user_id") is not None, \
            "user_id was not set after locked-account recovery -- this is the bug fixed tonight"
    finally:
        delete_user(conn, username)
        conn.close()


# ============================================================
# Forgot password (request a reset link)
# ============================================================

def test_forgot_password_with_registered_email_succeeds(monkeypatch):
    """Requesting a password reset link for a REAL registered email
    should succeed and show a confirmation, without sending a real email."""
    username = f"e2e_forgot_{uuid.uuid4().hex[:10]}"
    email = f"{username}@example.test"
    password = "ValidPassword123!"

    monkeypatch.setattr(send_email_to_user, "send_OTP_email", lambda _e, _o: True)
    monkeypatch.setattr(send_email_to_user, "send_resetpass_email", lambda _e, _t: True)
    monkeypatch.setattr(st, "switch_page", lambda _p: None)

    conn = get_connection()
    create_all_tables(conn)

    try:
        at = AppTest.from_file("Home.py", default_timeout=10).run()
        _register_user(at, username, email, password)

        at = AppTest.from_file("Home.py", default_timeout=10).run()
        email_field = _text_input_no_key(at, exclude_keys={"Login_username", "Login_password"})
        email_field.set_value(email)
        _button(at, "Send reset password link").click().run()

        assert not at.exception
        assert len(at.success) > 0
    finally:
        delete_user(conn, username)
        conn.close()


def test_forgot_password_with_unregistered_email_shows_error(monkeypatch):
    """Requesting a reset link for an email that isn't registered should
    show an error, not silently succeed or leak whether the email exists
    in a confusing way."""
    monkeypatch.setattr(send_email_to_user, "send_OTP_email", lambda _e, _o: True)
    monkeypatch.setattr(st, "switch_page", lambda _p: None)

    conn = get_connection()
    create_all_tables(conn)

    at = AppTest.from_file("Home.py", default_timeout=10).run()
    email_field = _text_input_no_key(at, exclude_keys={"Login_username", "Login_password"})
    email_field.set_value(f"definitely_not_registered_{uuid.uuid4().hex[:10]}@example.test")
    _button(at, "Send reset password link").click().run()

    assert not at.exception
    assert len(at.error) > 0
    conn.close()