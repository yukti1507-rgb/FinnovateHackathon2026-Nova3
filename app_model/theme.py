import streamlit as st
from app_model.users import get_user_theme
THEME_OPTIONS = {
    "Lavender":    {"bg": "#DDAFDD", "sidebar_bg": "#BC97BD", "text": "#29292c"},
    "Peach":       {"bg": "#FFCB9D", "sidebar_bg": "#F4AA92", "text": "#29292c"},
    "Mint":        {"bg": "#A9FFD7", "sidebar_bg": "#81B69C", "text": "#29292c"},
    "Sky Blue":    {"bg": "#A3E2FF", "sidebar_bg": "#759EB2", "text": "#29292c"},
    "Soft Pink":   {"bg": "#FFE9ED", "sidebar_bg": "#FFCED8", "text": "#29292c"},
    "Warm Sand":   {"bg": "#FFFFB5", "sidebar_bg": "#FFDBA0", "text": "#29292c"},
    "Dark Mode":   {"bg": "#1E1E1E", "sidebar_bg": "#787878", "text": "#F0F0F0"},
    "Light Mode":  {"bg": "#F3F3F3", "sidebar_bg": "#F0F2F6", "text": "#29292c"}
}


def apply_user_theme(conn, username):
    theme_name = get_user_theme(conn, username)
    theme = THEME_OPTIONS.get(theme_name, THEME_OPTIONS["Light Mode"])

    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {theme['bg']}; 
            color: {theme['text']} 
        }}
        section[data-testid="stSidebar"] {{
            background-color: {theme['sidebar_bg']};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )