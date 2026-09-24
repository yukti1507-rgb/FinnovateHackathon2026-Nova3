#profilepage

import streamlit as st
import os
from app_model.db import get_connection
from app_model.users import update_avatar, update_email, is_username_available, update_user, get_user, reset_password, get_user_info, delete_one_user, is_email_available, get_email, get_role
from app_model.display_avatar import display_avatar
from registration_and_login.hashing import is_valid_hash, generate_hash
from main import update_profile_pic, get_profile_pic
import time
from registration_and_login.send_email_to_user import OTP_initialisation, OTP_verification
from ui import apply_theme, navbar, require_login, page_header, MIST, NAVY

st.set_page_config(
    page_title="Profile",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="collapsed")

apply_theme()   # global theme + hides the sidebar

# page-specific CSS (your upload/avatar box sizing, recoloured)
st.markdown(f"""
<style>
div[data-testid="stFileUploader"] section {{
    padding: 10px;
    border-radius: 12px;
    background-color: {MIST};
}}
div[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
    min-height: 52px;
    border-radius: 12px;
    background-color: {MIST};
}}
.avatar-big {{ font-size: 4rem; line-height: 1; }}
</style>
""", unsafe_allow_html=True)

conn = get_connection()

# --- login check happens first, before anything else renders ---
require_login()
navbar(active="Profile")

page_header("Profile", "Manage your avatar, login details and account")
st.write("")

username = st.session_state.get('username')

# Directory for storing profile pictures
UPLOAD_DIR = "profile_pics"
os.makedirs(UPLOAD_DIR, exist_ok=True)

Avatar_options = ["🧑", "👩", "🐾", "🐼", "🐻", "🐺", "🐶", "🐸", "🐵", "🐴", "🐳", "🐲", "🐱", "🐰", "🐯", "🐭", "🐬", "🐣", "🐧", "🐨", "☯", "🐪", "🐦", "🐢", "🐠", "🐞", "🐝", "🐜", "🐚", "🐒", "🐇", "🐆", "🐅", "🧜‍♀️", "🦄", "👸", "💫", "🌸", "❤️‍🔥", "❄️", "👑", "🦉", "🐕", "🐈‍⬛"]

#displaying the current avatar/photo
chosen_avatar = display_avatar(conn, username)
saved_pic_path = get_profile_pic(username)

#display the user's username and email before changing it
current_username, current_email = get_user_info(conn, username)

left, right = st.columns([1, 1.6], gap="medium")

# ---------------- LEFT: avatar card ----------------
with left:
    with st.container(key="card_avatar"):
        a_col, info_col = st.columns([1, 2])
        with a_col:
            if saved_pic_path and os.path.exists(saved_pic_path):
                st.image(saved_pic_path, width=100)
            elif chosen_avatar:
                st.markdown(f'<div class="avatar-big">{chosen_avatar}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="avatar-big">👤</div>', unsafe_allow_html=True)
        with info_col:
            st.markdown(f'<p class="card-title" style="font-size:1.3rem;">{current_username}</p>'
                        f'<p class="muted">{current_email}</p>', unsafe_allow_html=True)

        st.divider()

        st.markdown("**Upload a profile picture**")
        uploaded_file = st.file_uploader(
            "Upload a profile picture",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )

        # only save once per new file - otherwise st.rerun() sees the same file
        # again and keeps saving + rerunning forever
        if uploaded_file and st.session_state.get("last_upload_id") != uploaded_file.file_id:
            save_path = os.path.join(UPLOAD_DIR, f"{username}.png")

            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            update_profile_pic(username, save_path)
            st.session_state["last_upload_id"] = uploaded_file.file_id

            st.success("Profile picture updated!")
            st.rerun()
        st.caption("If you upload a photo, it will be shown instead of your emoji avatar.")

        st.markdown("**Or choose an avatar**")

        if chosen_avatar in Avatar_options:
            i = Avatar_options.index(chosen_avatar)
        else:
            i = 0

        s_col, b_col = st.columns([2, 1])
        with s_col:
            selected_avatar = st.selectbox(
                "Choose an avatar",
                Avatar_options,
                index=i,
                label_visibility="collapsed"
            )
        with b_col:
            if st.button("Save avatar", use_container_width=True):
                update_avatar(conn, username, selected_avatar)
                st.success(" Avatar successfully updated.")
                st.rerun()

    st.write("")

    # ---------------- Session card (log out / exit) ----------------
    with st.container(key="card_session"):
        st.markdown('<p class="card-title">Session</p>', unsafe_allow_html=True)
        l_col, e_col = st.columns(2)
        with l_col:
            if st.button("Log out", use_container_width=True):
                st.session_state['confirm_logout'] = True
        with e_col:
            if st.button("Exit app", use_container_width=True):
                st.session_state['confirm_exit'] = True

        if st.session_state.get('confirm_logout'):
            st.warning("Do you wish to log out?")
            if st.button("Yes, log out", key="logout_yes"):
                st.session_state["Logged_in"] = False
                st.session_state["username"] = None
                st.session_state.pop('messages', None)
                st.session_state.pop('confirm_logout', None)
                st.switch_page("Home.py")

            if st.button("Cancel", key="logout_no"):
                st.session_state['confirm_logout'] = False
                st.rerun()

        if st.session_state.get('confirm_exit'):
            st.warning("Do you wish to end the connection (close the app)?")
            if st.button("Yes, exit", key="exit_yes"):
                st.info("Ending the connection. Please go back to VS Code.")
                time.sleep(2)
                os._exit(0)
            if st.button("Cancel", key="exit_no"):
                st.info("Exit cancelled.")
                st.session_state['confirm_exit'] = False
                st.rerun()

# ---------------- RIGHT: account settings card ----------------
with right:
    with st.container(key="card_settings"):
        st.markdown('<p class="card-title">Account settings</p>', unsafe_allow_html=True)
        st.write("")

        #change username
        with st.expander("Change username", icon=":material/badge:"):
            with st.form("change_username_form"):
                new_username = st.text_input("Please enter your new username.")
                submit_username = st.form_submit_button("Update username")

                if submit_username:
                    if not new_username:
                        st.error("Please enter your new username.")
                    elif new_username == username:
                        st.error("This is already your username.")
                        st.session_state["username_updated"] = False
                    elif not is_username_available(conn, new_username):
                        st.error("This username is taken. Please choose another username.")
                        st.session_state["username_updated"] = False
                    else:
                        update_user(conn, new_username, username)
                        st.session_state['username'] = new_username
                        st.session_state["username_updated"] = True
                        st.rerun()

            if st.session_state.get("username_updated"):
                st.success("𓂃🪶 Username updated! 𓂃🪶")
                st.session_state["username_updated"] = False   # reset so it doesn't loop forever
                time.sleep(1.5)
                st.rerun()

        #change email
        with st.expander("Change email", icon=":material/mail:"):
            with st.form("change_email", clear_on_submit=True):
                new_email = st.text_input("Please enter your new email")
                submit_email = st.form_submit_button("Update email")

                if submit_email:
                    if not new_email:
                        st.error("Please enter your new email.")
                    elif new_email == current_email:
                        st.error("This is your current email.")
                    elif "@" not in new_email or "." not in new_email:
                        st.error("Please enter a valid email address.")
                    elif not is_email_available(conn, new_email):
                        st.error("This email is already registered to another account.")
                    else:
                        update_email(conn, username, new_email)
                        st.success("𓆉⋆｡˚⋆❀ Email updated! ❀⋆｡˚⋆𓆉")

        #delete account
        with st.expander("Delete account", icon=":material/delete:"):
            st.write("Deletion of account is permanent. Do you wish to proceed?")

            role = get_role(conn, username)
            if role == "Admin":
                st.error("Cannot delete an admin account.")
            else:
                if 'confirm_delete' not in st.session_state:
                    st.session_state['confirm_delete'] = False

                if not st.session_state['confirm_delete']:
                    if st.button("Delete"):
                        st.session_state['confirm_delete'] = True
                        st.rerun()
                else:
                    st.warning("Are you sure you want to delete your account? Enter your password to delete your account.")
                    with st.form("delete_account_form"):
                        password = st.text_input("Password", type="password")
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            confirm_delete = st.form_submit_button("Delete Account")
                        with col2:
                            cancel_delete = st.form_submit_button("Cancel")

                        if confirm_delete:
                            user_data = get_user(conn, username)
                            id, user_name, user_hash, failed_attempts, locked = user_data
                            if is_valid_hash(password, user_hash):
                                delete_one_user(conn, username)
                                st.session_state["Logged_in"] = False
                                st.session_state["username"] = None
                                st.session_state['confirm_delete'] = False
                                st.success("Your account has been deleted")
                                time.sleep(2)
                                st.switch_page("Home.py")
                            else:
                                st.error("Password is incorrect. Unable to delete account.")

                        if cancel_delete:
                            st.session_state["confirm_delete"] = False
                            st.rerun()

        #change password using 2 step verification - asks for old password
        # (kept LAST because the OTP step calls st.stop(), which would hide anything below it)
        with st.expander("Change password", icon=":material/lock:"):
            with st.form("change_password_form", clear_on_submit=False):
                current_password = st.text_input("Please enter your current password.", type="password", help="Should be at least 12 characters")
                new_password = st.text_input("Please enter your new password.", type="password", help='Should be the same as the password entered above')
                confirm_new_password = st.text_input("Confirm new password.", type="password")
                submit_password = st.form_submit_button("Update password")

                if submit_password:
                    user_data = get_user(conn, username)
                    id, user_name, user_hash, failed_attempts, locked = user_data
                    if not new_password:
                        st.error("Please enter your new password.")
                    elif not is_valid_hash(current_password, user_hash):
                        st.error("Current password is incorrect.")
                    elif new_password == current_password:
                        st.error("Your new password cannot be the same as your current password.")
                    elif new_password != confirm_new_password:
                        st.error("New passwords do not match.")
                    elif len(new_password) < 12:
                        st.error("Password is too short. A secure password should be longer than 12 characters.")
                    else:
                        email = get_email(conn, username)
                        with st.spinner("Sending verification code to your email..."):
                            sending_OTP = OTP_initialisation(email)
                        if sending_OTP:
                            st.session_state['awaiting_otp'] = True
                            st.session_state['pending_new_hash'] = generate_hash(new_password)
                            st.rerun()
                        else:
                            st.error("Could not send verification email. Please try again.")
            if st.session_state.get('awaiting_otp'):
                st.info("A verification code has been sent to your email. Your code will expire in 5 minutes.")
                code_input = st.text_input("Enter the 6-digit code", key="otp_input", help='Check your email for a 6 digit code')

                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("Verify"):
                        with st.spinner("Verifying code..."):
                            ok, msg = OTP_verification(code_input)
                        if ok:
                            reset_password(conn, username, st.session_state['pending_new_hash'])
                            st.session_state.pop('awaiting_otp', None)
                            st.session_state.pop("pending_new_hash", None)
                            time.sleep(1)
                            st.success("˖° ✧ Password updated! ✧ °˖")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(msg)
                        st.stop()
                with col2:
                    if st.button("Cancel"):
                        st.session_state.pop('awaiting_otp', None)
                        st.session_state.pop('pending_username', None)
                        st.session_state.pop('otp_code', None)
                        st.session_state.pop('otp_email', None)
                        st.session_state.pop('otp_expires_at', None)
                        st.session_state.pop('otp_attempts', None)
                        st.rerun()
                st.stop()
