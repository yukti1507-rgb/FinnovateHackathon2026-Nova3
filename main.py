import streamlit as st
import string

def profile_icon():
    # Top bar layout: left empty, right for profile
    top_col1, top_col2 = st.columns([9, 1])  # adjust ratio for spacing

    with top_col1:
        st.empty()  # keeps left side blank

    with top_col2:
        # Show profile picture if available, else fallback avatar
        if "profile_pic" in st.session_state:
            st.image(st.session_state["profile_pic"], width=40)
        else:
            st.image("https://www.w3schools.com/howto/img_avatar.png", width=40)

        # Dropdown menu for actions
        action = st.selectbox(
            "👤",
            ["Select...", "View Profile", "Logout"],
            label_visibility="collapsed"
        )

        if action == "View Profile":
            st.switch_page("pages/User_Profile.py")   # must exist in pages/
        elif action == "Logout":
            st.session_state["logged_in"] = False
            st.switch_page("Home.py")

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