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
    /* ============================================================
       ACCESSIBILITY: visible focus outlines for keyboard navigation
       (screen reader / keyboard-only users need to SEE where focus
       is -- browsers often hide this by default in dark themes)
       ============================================================ */
    *:focus-visible {
        outline: 3px solid #0072B2 !important;
        outline-offset: 2px !important;
    }

    /* ============================================================
       ACCESSIBILITY: ensure minimum readable font sizes
       (WCAG recommends body text no smaller than 16px)
       ============================================================ */
    .stMarkdown p, .stMarkdown li, div[data-testid="stCaptionContainer"] {
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }

    /* ============================================================
       POLISH: card-style containers for metrics, expanders, info
       boxes -- gives a cleaner, more "designed" look with subtle
       depth instead of flat blocks
       ============================================================ */
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

    /* ============================================================
       POLISH: buttons -- slightly rounded, clear hover state
       (hover feedback also helps users confirm they're clicking
       the right thing -- an accessibility win, not just style)
       ============================================================ */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 114, 178, 0.25);
    }

    /* ============================================================
       ACCESSIBILITY: success/warning/error boxes -- add a left
       border stripe so status is visible by SHAPE, not just color
       (critical for colorblind users who may not distinguish the
       background color tint alone)
       ============================================================ */
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

    /* ============================================================
       POLISH: consistent section spacing so pages don't feel
       cramped or overly sparse
       ============================================================ */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.25rem;
    }

    /* ============================================================
       POLISH: sidebar (language picker) -- slightly distinguish it
       from main content so navigation feels intentional
       ============================================================ */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    </style>
    """, unsafe_allow_html=True)


def styled_section_header(emoji, title, subtitle=None):
    """
    A consistent, polished section header -- use instead of a bare
    st.subheader() for the main heading on each page/section, for a
    more "designed" look with an optional subtitle underneath.

    Example:
        styled_section_header("💸", "Where Your Money Goes", "A breakdown of your monthly spending")
    """
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
    A single-question help box -- NOT a persistent chat. The user
    types one question, gets one answer, using their real calculated
    data. No conversation history, no memory between questions.

    USAGE -- add near the top of any page, after inject_custom_css():

        from calculations.ui_style import help_question_widget
        from calculations.goals_ai import answer_user_question
        help_question_widget(dict(st.session_state), results)

    (`results` is whatever run_full_simulation() already returned on
    that page -- reuse it, don't recompute.)
    """
    from calculations.goals_ai import answer_user_question

    with st.expander("❓ " + "Ask a question about your finances"):
        st.caption("Ask about your goals, loans, or spending shown in this app.")
        question = st.text_input("Your question", key="help_question_input", label_visibility="collapsed", placeholder="e.g. How am I doing on my Laptop goal?")

        if st.button("Ask", key="help_question_button"):
            if question.strip() == "":
                st.warning("Please type a question first.")
            else:
                with st.spinner("Thinking..."):
                    answer = answer_user_question(question, user_data, results)
                st.info(answer)