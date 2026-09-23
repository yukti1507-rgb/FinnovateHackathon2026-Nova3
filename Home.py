import streamlit as st
from pathlib import Path
from registration_and_login.hashing import generate_hash, is_valid_hash
from app_model.db import get_connection
from main import password_requirements
#users have not been decided yet - do necessary changes when decided
from app_model.users import set_token, get_user_by_token, reset_password, is_username_available, add_user, update_login_attempts, get_user, reset_login, is_email_available, get_email, get_role

from calculations.language import show_language_picker, t

from app_model.schema import create_user_table, create_user_profile,alter_users_login_table
from registration_and_login.send_email_to_user import send_resetpass_email, OTP_initialisation, OTP_verification

#very ugly in coursework - needs improvement
#from app_model.theme import apply_user_theme
import time
import re

conn = get_connection()
create_user_table(conn)
create_user_profile(conn)
alter_users_login_table(conn)

#theme
#apply_user_theme(conn, st.session_state.get('username'))

st.set_page_config(
    page_title = "Can I Afford My Financial ",
    page_icon = "💡",
    layout = "wide"
    )

show_language_picker()

# --- minor CSS polish for the auth panel ---
st.markdown(
    """
    <style>
    div[data-testid="stExpander"] summary p {
        color: #2ED3C7 !important;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1 style='color:#2ED3C7;'>Welcome to Future Me!</h1>", unsafe_allow_html=True)
token = st.query_params.get("token")

if token:
    st.title("Reset your password")
    username = get_user_by_token(conn, token)
    if username is None:
        st.error("This link is invalid or expired. Please request a new one.")
        if st.button("Go back to login"):
            st.query_params.clear()
            st.rerun()
    else:
        with st.form("Reset password"):
            new_password = st.text_input("New Password", type = "password")
            confirm_password = st.text_input("Confirm Password", type = "password")
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


if 'Logged_in' not in st.session_state:
    st.session_state['Logged_in'] = False
if 'auth_view' not in st.session_state:
    st.session_state['auth_view'] = 'login'  # 'login' or 'register'


 # --- layout: empty/hero space on the left, narrow auth panel on the right ---
hero_col, auth_col = st.columns([2, 1], gap= "medium")

with hero_col:
    hero_image_path = Path(__file__).parent / "assets" / "image.png"  # swap this for your image filename
    if hero_image_path.exists():
        st.image(str(hero_image_path), use_container_width=True)
    else:
        st.write("")  # falls back to empty space if the hero image isn't found
with auth_col:
    if st.session_state["auth_view"] == "login":
        #login form containing username, password and eventually otp code
        with st.form("login_form", clear_on_submit=False):   
            st.markdown("<h3 style='color:#2ED3C7;'>Log in</h3>", unsafe_allow_html=True)
            login_username = st.text_input("Username", key="Login_username",
            placeholder="Username", label_visibility="collapsed")
            login_password = st.text_input("Password", type="password", key="Login_password",
                    placeholder="Password", label_visibility="collapsed")
            submit_login = st.form_submit_button("Log in")

            if submit_login:
                user_login = get_user(conn, login_username)

                if user_login is None:
                    #if the person hasnt entered either the login or password
                    st.error("Incorrect login. Please try again.")
                    st.session_state['Logged_in'] = False
                else:
                    id,user_name, user_hash, failed_attempts, locked = user_login
                    if locked:
                        #checks if the users account has already been locked due to too many incorrect passwords
                        st.error("Too many failed attempts. Please use 'forgot password' to reset password.")
                        st.session_state['Logged_in'] = False
                    elif login_username == user_name and is_valid_hash(login_password, user_hash):
                        #if the user is not locked and has the correct username or paswword they enter this part
                        reset_login(conn, login_username)
                        email = get_email(conn, login_username)
                        with st.spinner("Sending verification code to your email..."):
                            #sending the otp to the user
                            sending_OTP =  OTP_initialisation(email)
                        if sending_OTP:
                            st.session_state['awaiting_otp'] = True
                            st.session_state['pending_username'] = user_name
                            st.rerun()
                        else:
                            st.error("Could not send verification email. Please try again.")   
                    else:
                        st.error("Incorrect username or password. Please try again")
                        #resets login attempts if the user is able to enter the correct login within 3 tries so that the next time they still have 3 chances to guess the login
                        update_login_attempts(conn, login_username)
                        st.session_state['Logged_in'] = False

    if st.session_state.get('awaiting_otp'):
        st.info(f"A verification code has been sent to your email. Your code will expire in 5 minutes.")
        st.caption("For your security, this app has a 2 step verification code. Please verify your identity by entering the code sent to your email.")
        code_input = st.text_input(
                "Enter the 6-digit code", key="otp_input",
                placeholder="6-digit code", help="Check your email for a 6 digit code"
            )
        otp_col1, otp_col2 = st.columns(2)
        with otp_col1:
            if st.button("Verify", use_container_width=True):
                with st.spinner("Verifying code..."):
                    #calls function which checks if it is the right otp
                    ok, msg = OTP_verification(code_input)
                if ok:
                    st.session_state['Logged_in'] = True
                    st.session_state['username'] = st.session_state["pending_username"]
                    #checks if an admin has logged in
                    role = get_role(conn, st.session_state['username'])
                    if role == "Admin":
                        st.session_state['Admin'] = True
                    else:
                        st.session_state['Admin'] = False
                    st.session_state.pop('awaiting_otp', None)
                    st.success("Logged in successfully")
                    time.sleep(2)
                    st.switch_page("pages/2_Cyber_Incident_Dashboard.py")
                else:
                    st.error(msg)
                st.stop()
        with otp_col2:
            #cancel button if the user entered the wrong username - then the otp will be directed to someone else's email
            if st.button("Cancel", use_container_width=True):
                st.session_state.pop('awaiting_otp', None)
                st.session_state.pop('pending_username', None)
                st.session_state.pop('otp_code', None)
                st.session_state.pop('otp_email', None)
                st.session_state.pop('otp_expires_at', None)
                st.session_state.pop('otp_attempts', None)
                st.rerun()
        st.stop()
    #if user forgot their password
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

        st.write("")
        st.markdown("<p style='color:#2ED3C7;'>Don't have an account yet?</p>", unsafe_allow_html=True)
        if st.button("Register", use_container_width=True):
            st.session_state['auth_view'] = 'register'
            st.rerun()            
        else:
            with st.form("register_form", clear_on_submit=False):
                st.subheader("Register")
                register_username = st.text_input(
                    "New Username", placeholder="Username", label_visibility="collapsed"
                )
                register_email = st.text_input(
                    "Email", placeholder="Email", label_visibility="collapsed"
                )
                register_password = st.text_input(
                    "New Password", type="password", placeholder="Password", label_visibility="collapsed"
                )
                confirm_password = st.text_input(
                    "Confirm Password", type="password", placeholder="Confirm password", label_visibility="collapsed"
                )
    
                # Show feedback on password after typing
                if register_password:
                    password_requirements(register_password)
    
                submitted = st.form_submit_button("Register", use_container_width=True)
    
                if submitted:
                    #Check validation of password
                    if not register_username or not register_email or not register_password or not confirm_password:
                        st.error("You are required to fill in all fields")
                    elif register_password != confirm_password:
                        st.error("Passwords do not match. Please try again.")
                    elif not all([
                        len(register_password) >= 8,
                        re.search(r"[A-Z]", register_password),
                        re.search(r"\d", register_password),
                        re.search(r"[^\w\s]|_", register_password)
                    ]):
                        st.error("Password must meet all requirements above.")
                    else:
                        # Save user in databse
                        hash_password = generate_hash(register_password)
                        add_user(conn, register_username, hash_password, register_email)
    
                        #Also append user to users.txt file
                        with open("DATA/users.txt", "a") as f:
                            f.write(f"{register_username},{hash_password}\n")
    
                        #Update st.sesion_state
                        st.session_state["current_user"] = register_username
                        st.session_state["current_email"] = register_email
                        st.session_state["logged_in"] = False
    
                        st.success(f"Registration successful, {register_username}! Please log in.")
 
        st.write("")
        st.markdown("Already have an account?")
        if st.button("Log in", use_container_width=True):
            st.session_state['auth_view'] = 'login'
            st.rerun()        


