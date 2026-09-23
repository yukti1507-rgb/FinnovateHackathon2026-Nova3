"""
Shared UI/UX + accessibility styling for the whole app.

WHY THIS FILE EXISTS:
Instead of rewriting every page's layout (risky this late, and your
teammate is already working on aesthetics separately), this module is
ADDITIVE: one import + one function call at the top of each page adds
consistent, accessible styling app-wide, without touching your
existing layout code or logic.

USAGE -- add these 2 lines near the top of every page, right after
show_language_picker():

    from calculations.ui_style import inject_custom_css
    inject_custom_css()

That's it. Everything below is just CSS injected via st.markdown.
"""

import streamlit as st


def inject_custom_css():
    st.markdown("""
    <style>
    *:focus-visible {
        outline: 3px solid #0072B2 !important;
        outline-offset: 2px !important;
    }

    .stMarkdown p, .stMarkdown li, div[data-testid="stCaptionContainer"] {
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }

    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
    }

    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 114, 178, 0.25);
    }

    div[data-testid="stAlertContentSuccess"] {
        border-left: 5px solid #009E73 !important;
        padding-left: 12px !important;
    }
    div[data-testid="stAlertContentWarning"] {
        border-left: 5px solid #E69F00 !important;
        padding-left: 12px !important;
    }
    div[data-testid="stAlertContentError"] {
        border-left: 5px solid #D55E00 !important;
        padding-left: 12px !important;
    }
    div[data-testid="stAlertContentInfo"] {
        border-left: 5px solid #0072B2 !important;
        padding-left: 12px !important;
    }

    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.25rem;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    </style>
    """, unsafe_allow_html=True)


def styled_section_header(emoji, title, subtitle=None):
    st.markdown(f"""
    <div style="margin-bottom: 0.5rem;">
        <span style="font-size: 1.4rem;">{emoji}</span>
        <span style="font-size: 1.4rem; font-weight: 700; margin-left: 0.4rem;">{title}</span>
    </div>
    """, unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def help_question_widget(user_data, results):
    """
    A single-question help box -- NOT a persistent chat.
    """
    from calculations.goals_ai import answer_user_question
    from calculations.language import t

    with st.expander("❓ " + t("Ask a question about your finances")):
        st.caption(t("Ask about your goals, loans, or spending shown in this app."))
        question = st.text_input(
            t("Your question"), key="help_question_input",
            label_visibility="collapsed",
            placeholder=t("e.g. How am I doing on my Laptop goal?")
        )

        if st.button(t("Ask"), key="help_question_button"):
            if question.strip() == "":
                st.warning(t("Please type a question first."))
            else:
                with st.spinner(t("Thinking...")):
                    answer = answer_user_question(question, user_data, results)
                st.info(answer)