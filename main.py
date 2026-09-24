import string
import os
import streamlit as st
from app_model.db import get_connection

conn = get_connection()
def password_strength(password):
    score = 0
    length = len(password)

    upper_case = any(c.isupper() for c in password)
    lower_case = any(c.islower() for c in password)
    special = any(c in string.punctuation for c in password)
    digits = any(c.isdigit() for c in password)

    characters = [upper_case, lower_case, special, digits]

    if length > 8:
        score += 1
    if length > 12:
        score += 1
    if length > 17:
        score += 1
    if length > 20:
        score += 1

    score += sum(characters) - 1

    if score < 4:
        return "Weak", score
    elif score == 4:
        return "Okay", score
    elif 4 < score < 6:
        return "Good", score
    else:
        return "Strong", score

def feedback(password):
    strength, score = password_strength(password)
    feedback = f"Password strength: {strength} (Score: {score}/7)\n"

    if score < 4:
        feedback += "\nSuggestions to improve your password:\n"
        if len(password) <= 8:
            feedback += "- Make your password longer (more than 8 characters).\n"
        if not any(c.isupper() for c in password):
            feedback += "- Include uppercase letters.\n"
        if not any(c.islower() for c in password):
            feedback += "- Include lowercase letters.\n"
        if not any(c in string.punctuation for c in password):
            feedback += "- Add special characters (e.g., @, #, $).\n"
        if not any(c.isdigit() for c in password):
            feedback += "- Add numbers.\n"

    return feedback


def password_requirements(password: str):
    requirements = {
        "At least 8 characters": len(password) >= 8,
        "At least one uppercase letter": any(c.isupper() for c in password),
        "At least one lowercase letter": any(c.islower() for c in password),
        "At least one number": any(c.isdigit() for c in password),
        "At least one special symbol": any(c in string.punctuation for c in password),
    }

    st.write("### Password Requirements")
    for req, met in requirements.items():
        if met:
            # Fade out satisfied requirements
            st.markdown(f"<span style='color:lightgrey'>✔ {req}</span>", unsafe_allow_html=True)
        else:
            # Keep unmet requirements in red
            st.markdown(f"<span style='color:red'>✘ {req}</span>", unsafe_allow_html=True)

    if all(requirements.values()):
        st.success("✅ Your password meets all requirements.")

def profile_icon():
    top_col1, top_col2 = st.columns([9, 1])

    with top_col1:
        st.empty()

    with top_col2:
        username = st.session_state.get('username')
        saved_pic_path = get_profile_pic(username) if username else None

        if saved_pic_path and os.path.exists(saved_pic_path):
            st.image(saved_pic_path, width=40)
        else:
            st.image("https://www.w3schools.com/howto/img_avatar.png", width=40)

        is_admin = st.session_state.get("Admin", False)
        menu_options = ["Select...", "View Profile", "Logout"]
        if is_admin:
            menu_options.insert(1, "Admin Dashboard")

        action = st.selectbox(
            "👤",
            menu_options,
            label_visibility="collapsed"
        )

        if action == "View Profile":
            st.switch_page("pages/1_Profile.py")
        elif action == "Admin Dashboard":
            st.switch_page("pages/_Admin.py")
        elif action == "Logout":
            st.session_state["Logged_in"] = False
            st.session_state["username"] = None
            st.session_state["Admin"] = False
            st.switch_page("Home.py")

def update_profile_pic(username, file_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE user_profile SET profile_pic = ?
        WHERE user_id = (SELECT id FROM users_login WHERE username = ?)
    ''', (file_path, username))
    conn.commit()
    conn.close()

def get_profile_pic(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.profile_pic FROM user_profile p
        JOIN users_login u ON p.user_id = u.id
        WHERE u.username = ?
    ''', (username,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result and result[0] else None