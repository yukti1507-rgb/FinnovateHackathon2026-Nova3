# Home.py - landing page with logo + login form (no navbar, no sidebar)

import streamlit as st
from pathlib import Path
from registration_and_login.hashing import generate_hash, is_valid_hash
from app_model.db import get_connection
from app_model.schema import create_all_tables
from main import password_requirements
#users have not been decided yet - do necessary changes when decided
from app_model.users import record_blocked_login, record_successful_login, set_token, get_user_by_token, reset_password, is_username_available, add_user, update_login_attempts, get_user, reset_login, is_email_available, get_email, get_role

from calculations.language import show_language_picker, t

from app_model.schema import create_audit_table, create_user_table, create_user_profile,alter_users_login_table
from registration_and_login.send_email_to_user import send_resetpass_email, OTP_initialisation, OTP_verification

import time
import re

from ui import apply_theme, show_logo, display_settings, DEEP, BLUE, NAVY, MIST

# set_page_config must be the first Streamlit command
st.set_page_config(
    page_title="Can I Afford My Financial",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)
apply_theme()   # global theme + hides the sidebar

conn = get_connection()
create_all_tables(conn)

# where to go after a successful login
DASHBOARD_PAGE = "pages/Dashboard.py"

# already logged in? skip straight to the dashboard
if st.session_state.get("Logged_in") and st.session_state.get("username"):
    st.switch_page(DASHBOARD_PAGE)

# ---------- page-specific CSS ----------
st.markdown(f"""
<style>
.hero {{
    border-radius: 28px; padding: 42px 40px; color: #fff; min-height: 520px;
    background:
        radial-gradient(circle at 88% 18%, {BLUE} 0 16%, transparent 17%),
        radial-gradient(circle at 100% 100%, {DEEP} 0 38%, transparent 39%),
        linear-gradient(150deg, {NAVY}, {DEEP});
    display: flex; flex-direction: column; justify-content: flex-end;
}}
.stApp .hero h1 {{ color: #fff !important; font-size: 2.6rem; font-weight: 800; line-height: 1.1; margin: 0 0 14px; max-width: 14ch; }}
.stApp .hero p {{ color: rgba(255,255,255,.85) !important; font-size: 1.05rem; max-width: 40ch; margin: 0; }}
.hero-stats {{ display: flex; gap: 12px; margin-top: 28px; flex-wrap: wrap; }}
.stApp .hero-stats div {{ color: #fff; background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.18);
                   border-radius: 14px; padding: 10px 14px; font-size: .9rem; }}
.st-key-card_login {{ margin-top: 10px; }}
.auth-title {{ color: {NAVY}; font-weight: 800; font-size: 1.5rem; margin: 6px 0 2px; }}
.auth-sub {{ color: {BLUE}; font-weight: 700; font-size: 1.15rem; margin: 0 0 6px; }}
div[data-testid="stExpander"] summary p {{ color: {DEEP} !important; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

if 'Logged_in' not in st.session_state:
    st.session_state['Logged_in'] = False
if 'auth_view' not in st.session_state:
    st.session_state['auth_view'] = 'login'  # 'login' or 'register'

token = st.query_params.get("token")

# --- layout: hero on the left, login card on the right ---
# accessibility / display mode button, top right
_, settings_col = st.columns([6, 1])
with settings_col:
    display_settings()

hero_col, auth_col = st.columns([1.3, 1], gap="large")

with hero_col:
    st.markdown("""
<div class="hero">
  <h1>Know if you can afford your goals</h1>
  <p>Track your income, test a loan before you take it, and see how many months each goal will take.</p>
  <div class="hero-stats">
    <div>🎯 Goal timelines</div><div>🏦 Loan affordability</div><div>📈 Savings forecast</div>
  </div>
</div>""", unsafe_allow_html=True)

with auth_col:
    with st.container(key="card_login"):
        show_logo(width=150)          # your logo (set LOGO_PATH in ui.py)
        st.markdown('<p class="auth-title">Welcome to Future Me!</p>', unsafe_allow_html=True)

        # ================= RESET PASSWORD (from email link) =================
        if token:
            st.markdown('<p class="auth-sub">Reset your password</p>', unsafe_allow_html=True)
            username = get_user_by_token(conn, token)
            if username is None:
                st.error("This link is invalid or expired. Please request a new one.")
                if st.button("Go back to login"):
                    st.query_params.clear()
                    st.rerun()
            else:
                with st.form("Reset password"):
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    submit_reset = st.form_submit_button("Reset password")

                    if submit_reset:
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 12:
                            st.error("Password is too short. A secure password should be longer than 12 characters.")
                        else:
                            new_hash_password = generate_hash(new_password)
                            reset_password(conn, username, new_hash_password)
                            st.success("Password has been reset. Please log in.")

                if st.button("Go back to login"):
                    st.query_params.clear()
                    st.rerun()

            st.stop()

        # ============================ LOGIN VIEW ============================
        if st.session_state["auth_view"] == "login":

            # ---------- Locked account: message + a button the user must click to request an OTP ----------
            if st.session_state.get('account_is_locked') and not st.session_state.get('awaiting_otp') and not st.session_state.get('otp_verified'):
                st.error("🔒 Your account has been locked out after 3 failed attempts.")
                st.caption("To regain access, request a verification code sent to your registered email. You'll be able to set a new password once verified.")

                if st.button("Send me a verification code", use_container_width=True, type="primary"):
                    email = get_email(conn, st.session_state['locked_username'])
                    if not email:
                        st.error("No email address is registered for this account.")
                    else:
                        with st.spinner("Sending verification code to your email..."):
                            sending_OTP = OTP_initialisation(email)
                        if sending_OTP:
                            st.session_state['awaiting_otp'] = True
                            st.session_state['pending_username'] = st.session_state['locked_username']
                            # This OTP is for LOCKOUT RECOVERY -- after verifying, the
                            # user must be forced to set a brand new password.
                            st.session_state['otp_reason'] = 'locked'
                            st.rerun()
                        else:
                            st.error("Could not send verification email. Please try again.")
                            st.caption(st.session_state.get("email_error", ""))

                if st.button("Back to login", use_container_width=True):
                    st.session_state.pop('account_is_locked', None)
                    st.session_state.pop('locked_username', None)
                    st.rerun()

                st.stop()

            # ---------- Login form ----------
            if not st.session_state.get('awaiting_otp') and not st.session_state.get('otp_verified'):
                with st.form("login_form", clear_on_submit=False):
                    st.markdown('<p class="auth-sub">Log in</p>', unsafe_allow_html=True)
                    login_username = st.text_input("Username", key="Login_username",
                        placeholder="Username", label_visibility="collapsed")
                    login_password = st.text_input("Password", type="password", key="Login_password",
                        placeholder="Password", label_visibility="collapsed")
                    submit_login = st.form_submit_button("Log in", use_container_width=True)

                    if submit_login:
                        user_login = get_user(conn, login_username)

                        if user_login is None:
                            st.error("Incorrect login. Please try again.")
                            st.session_state['Logged_in'] = False
                        else:
                            id, user_name, user_hash, failed_attempts, locked = user_login

                            if locked:
                                # already locked from before — record the blocked attempt, show lockout screen, do NOT auto-send OTP
                                record_blocked_login(conn, login_username)
                                st.session_state['account_is_locked'] = True
                                st.session_state['locked_username'] = user_name
                                st.rerun()

                            elif login_username == user_name and is_valid_hash(login_password, user_hash):
                                # Every login requires OTP verification (mandatory 2FA).
                                # record_successful_login() and reset_login() are called
                                # only AFTER the OTP is verified (otp_reason == 'login').
                                email = get_email(conn, user_name)
                                if not email:
                                    st.error("No email address is registered for this account. Cannot send verification code.")
                                else:
                                    with st.spinner("Sending verification code to your email..."):
                                        sending_OTP = OTP_initialisation(email)
                                    if sending_OTP:
                                        st.session_state['awaiting_otp'] = True
                                        st.session_state['pending_username'] = user_name
                                        st.session_state['otp_reason'] = 'login'
                                        st.rerun()
                                    else:
                                        st.error("Could not send verification email. Please try again.")

                            else:
                                # wrong password — increment attempts, then check whether this attempt just locked the account
                                update_login_attempts(conn, login_username)
                                updated = get_user(conn, login_username)
                                _, _, _, updated_attempts, updated_locked = updated

                                if updated_locked:
                                    # this was the 3rd failed attempt — show lockout screen, do NOT auto-send OTP
                                    st.session_state['account_is_locked'] = True
                                    st.session_state['locked_username'] = user_name
                                    st.rerun()
                                else:
                                    attempts_left = 3 - updated_attempts
                                    st.error(
                                        f"Incorrect username or password. You have {attempts_left} "
                                        f"attempt{'s' if attempts_left != 1 else ''} remaining before your account is locked."
                                    )

                                st.session_state['Logged_in'] = False

            # ---------- OTP verification step ----------
            # Shared by TWO flows, distinguished by st.session_state['otp_reason']:
            #   'locked' -> after verifying, the user must set a brand new password
            #   'login'  -> after verifying, this completes an ordinary login (2FA)
            if st.session_state.get('awaiting_otp') and not st.session_state.get('otp_verified'):
                st.info("A verification code has been sent to your email. Your code will expire in 5 minutes.")
                st.caption("For your security, we need to verify your identity to continue.")

                code_input = st.text_input(
                    "Enter the 6-digit code", key="otp_input",
                    placeholder="Enter the 6-digit code from your email",
                    help="Check your email for a 6 digit code"
                )
                otp_col1, otp_col2 = st.columns(2)
                with otp_col1:
                    if st.button("Verify", use_container_width=True):
                        with st.spinner("Verifying code..."):
                            ok, msg = OTP_verification(code_input)
                        if ok:
                            if st.session_state.get('otp_reason') == 'login':
                                # Ordinary 2FA login -- complete it now, no forced reset.
                                username = st.session_state["pending_username"]
                                user_data = get_user(conn, username)

                                if user_data is None:
                                    st.error("Unable to load your account information. Please try again.")
                                    st.stop()

                                user_id = user_data[0]

                                record_successful_login(conn, username)
                                reset_login(conn, username)

                                st.session_state["Logged_in"] = True
                                st.session_state["username"] = username
                                st.session_state["user_id"] = user_id

                                role = get_role(conn, username)
                                st.session_state["Admin"] = (role == "Admin")

                                st.session_state.pop("awaiting_otp", None)
                                st.session_state.pop("pending_username", None)
                                st.session_state.pop("otp_reason", None)

                                st.success("Logged in successfully")
                                time.sleep(1)
                                st.switch_page(DASHBOARD_PAGE)
                            else:
                                # Lockout recovery -- go to the mandatory password-reset step below.
                                st.session_state['otp_verified'] = True
                                st.rerun()
                        else:
                            st.error(msg)
                        st.stop()
                with otp_col2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.pop('awaiting_otp', None)
                        st.session_state.pop('pending_username', None)
                        st.session_state.pop('otp_verified', None)
                        st.session_state.pop('otp_reason', None)
                        st.session_state.pop('account_is_locked', None)
                        st.session_state.pop('locked_username', None)
                        st.session_state.pop('otp_code', None)
                        st.session_state.pop('otp_email', None)
                        st.session_state.pop('otp_expires_at', None)
                        st.session_state.pop('otp_attempts', None)
                        st.rerun()
                st.stop()

            # ---------- Post-verification: set a new password (mandatory, since the account was locked) ----------
            if st.session_state.get('otp_verified'):
                st.success("Identity verified.")
                st.warning("Since your account was locked, please set a new password to continue.")

                with st.form("set_new_password_form"):
                    new_password = st.text_input("New password", type="password", help="Should be at least 12 characters")
                    confirm_new_password = st.text_input("Confirm new password", type="password")
                    submit_new_password = st.form_submit_button("Set password & log in", use_container_width=True)

                    if submit_new_password:
                        if not new_password:
                            st.error("Please enter a new password.")
                        elif new_password != confirm_new_password:
                            st.error("Passwords do not match.")
                        elif len(new_password) < 12:
                            st.error("Password is too short. A secure password should be longer than 12 characters.")
                        else:
                            # reset_password clears the hash, failed_attempts, and locked flag together
                            reset_password(conn, st.session_state["pending_username"], generate_hash(new_password))
                            username = st.session_state["pending_username"]

                            user_data = get_user(conn, username)
                            user_id = user_data[0] if user_data else None

                            st.session_state['Logged_in'] = True
                            st.session_state['username'] = username
                            st.session_state['user_id'] = user_id
                            role = get_role(conn, username)
                            st.session_state['Admin'] = (role == "Admin")
                            st.session_state.pop('awaiting_otp', None)
                            st.session_state.pop('otp_verified', None)
                            st.session_state.pop('otp_reason', None)
                            st.session_state.pop('account_is_locked', None)
                            st.session_state.pop('locked_username', None)
                            st.success("Password updated — logging you in.")
                            time.sleep(1)
                            st.switch_page(DASHBOARD_PAGE)
                st.stop()

            # ---------- Forgot password ----------
            if not st.session_state.get('account_is_locked') and not st.session_state.get('awaiting_otp') and not st.session_state.get('otp_verified'):
                with st.expander("Forgot password"):
                    with st.form("Forgot_password"):
                        email = st.text_input("Please enter your email")
                        submit_email = st.form_submit_button("Send reset password link")

                        if submit_email:
                            if not email:
                                st.error("Please enter your email.")
                            else:
                                reset_token = set_token(conn, email)
                                if reset_token is None:
                                    st.error("There is no account with that email")
                                else:
                                    with st.spinner("Sending email to reset password..."):
                                        sending_reset_psw = send_resetpass_email(email, reset_token)
                                    if sending_reset_psw:
                                        st.success("Link successfully sent")
                                    else:
                                        st.error("Something went wrong when sending the email. Please try again.")

                # Register prompt
                st.write("")
                st.markdown('<p class="muted">Don\'t have an account yet?</p>', unsafe_allow_html=True)
                if st.button("Register instead", use_container_width=True):
                    st.session_state['auth_view'] = 'register'
                    st.rerun()

        # ========================== REGISTER VIEW ==========================
        elif st.session_state["auth_view"] == "register":
            st.markdown('<p class="auth-sub">Create an account</p>', unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=False):
                register_username = st.text_input("New Username", placeholder="Username", label_visibility="collapsed")
                register_email = st.text_input("Email", placeholder="Email", label_visibility="collapsed")
                register_password = st.text_input("New Password", type="password", placeholder="Password", label_visibility="collapsed")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password", label_visibility="collapsed")

                if register_password:
                    password_requirements(register_password)

                submitted = st.form_submit_button("Register", use_container_width=True)

                if submitted:
                    if not register_username or not register_email or not register_password or not confirm_password:
                        st.error("You are required to fill in all fields")
                    elif "@" not in register_email or "." not in register_email:
                        st.error("Please enter a valid email address.")
                    elif register_password != confirm_password:
                        st.error("Passwords do not match. Please try again.")
                    elif not all([
                        len(register_password) >= 12,
                        re.search(r"[A-Z]", register_password),
                        re.search(r"\d", register_password),
                        re.search(r"[^\w\s]|_", register_password)
                    ]):
                        st.error("Password must meet all requirements above.")
                    elif not is_username_available(conn, register_username):
                        st.error("This username is taken. Please choose another.")
                    elif not is_email_available(conn, register_email):
                        st.error("This email is already registered.")
                    else:
                        hash_password = generate_hash(register_password)
                        add_user(conn, register_username, hash_password, register_email)
                        st.success(f"Registration successful, {register_username}! Please log in.")
                        st.session_state['auth_view'] = 'login'
                        time.sleep(1.5)
                        st.rerun()

            st.write("")
            st.markdown('<p class="muted">Already have an account?</p>', unsafe_allow_html=True)
            if st.button("Log in instead", use_container_width=True):
                st.session_state['auth_view'] = 'login'
                st.rerun()