# pages/3_Goals.py - "Your Financial Future": will you reach each goal on time?

import streamlit as st
import plotly.graph_objects as go
from calculations.projections import run_full_simulation
from calculations.goals_ai import simulate_savings_increase, explain_goals
from calculations.language import show_language_picker, t
from calculations.goals import inflating_target_over_time
from calculations.savings import project_savings
from calculations.ui_style import help_question_widget

from calculations.gamification import (
    calculate_goal_progress,
    get_goal_stage,
    get_stage_name,
    get_current_milestone,
    get_next_milestone,
    check_for_new_milestone,
    get_milestone_message,
)
from calculations.gamification_ai import generate_ai_financial_message
from calculations.goal_allocation import (
    calculate_goal_allocation,
    calculate_projected_completion,
)
from app_model.money import to_cents, from_cents

st.set_page_config(
    page_title="Your Goals",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from ui import (apply_theme, navbar, require_login, page_header, safe_link, style_fig,
                stat_card, badge, money, FINANCES_PAGE)

apply_theme()
require_login()
navbar(active="Goals")

show_language_picker()

page_header(t("Your Financial Future"), t("Will you reach each goal on time? Here's what your savings say."))
st.write("")

# ---------- nothing filled in yet ----------
if "income" not in st.session_state:
    with st.container(key="card_empty"):
        st.markdown(f'<p class="card-title">{t("Please fill in your details first.")}</p>', unsafe_allow_html=True)
        st.caption(t("Add your income, expenses and goals, then come back here."))
        safe_link(FINANCES_PAGE, t("Go to Your Finances"), ":material/edit:")
    st.stop()

results = run_full_simulation(st.session_state, months=60)
goals_status = results.get("goals_status") or []

# ---------- summary numbers ----------
reached = sum(1 for g in goals_status if g["reached"])
behind = len(goals_status) - reached

c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1:
    stat_card("s_goals", t("Goals"), len(goals_status))
with c2:
    stat_card("s_reached", t("On track"), reached)
with c3:
    stat_card("s_behind", t("Need attention"), behind)
with c4:
    if "loan_summary" in results:
        stat_card("s_interest", t("Total interest on loan"),
                  f"Rs {results['loan_summary']['total_interest']}")
    else:
        stat_card("s_saving", t("Saving per month"), money(st.session_state.get("monthly_savings", 0)))

st.write("")

help_question_widget(dict(st.session_state), results)

# ============================================================
# GOAL ALLOCATION -- deterministic split of savings across goals
# (No AI here -- pure Python, based on deadline + amount needed.
# This is a PLANNING SUGGESTION only; it doesn't move real money.)
# ============================================================

current_savings_cents = to_cents(st.session_state.get("current_savings", 0.0))
monthly_savings_cents = to_cents(st.session_state.get("monthly_savings", 0.0))

allocation_goals = []
for goal in goals_status:
    allocation_goals.append({
        "id": goal["name"],  # session_state goals have no numeric id -- name is unique enough here
        "name": goal["name"],
        "target_cents": to_cents(goal["amount"]),
        "current_cents": 0,  # this app tracks one shared savings pool, not per-goal earmarked amounts
        "months_remaining": goal["deadline_months"],
        "priority": 0,  # session_state goals don't carry a priority field -- treated equally
    })

allocation_results = calculate_goal_allocation(
    allocation_goals, current_savings_cents, monthly_savings_cents
) if allocation_goals else []

if allocation_results:
    st.write("")
    with st.container(key="card_allocation"):
        st.markdown(f'<p class="card-title">💰 {t("How your savings could be distributed")}</p>', unsafe_allow_html=True)
        st.caption(t(
            "This is a planning suggestion based on your goals and deadlines. "
            "It does not move or change your actual savings."
        ))

        alloc_col1, alloc_col2 = st.columns(2)
        with alloc_col1:
            st.metric(t("Available savings"), f"Rs {from_cents(current_savings_cents):,.2f}")
        with alloc_col2:
            st.metric(t("Available monthly savings"), f"Rs {from_cents(monthly_savings_cents):,.2f}")

# ---------- one card per goal ----------
if goals_status:
    st.subheader(t("🎯 Your Goals"))

    for i, goal in enumerate(goals_status):
        actual_months = results["actual_months_per_goal"][goal["name"]]
        real_target = results["inflation_adjusted_target_per_goal"][goal["name"]]

        # -------- find this goal's suggested allocation --------
        allocation_item = next((a for a in allocation_results if a["name"] == goal["name"]), None)

        with st.container(key=f"card_goal_{i}"):
            # title row: goal name + status badge (icon + word, not only colour)
            if goal["reached"]:
                status = badge("good", t("On track"))
            elif actual_months is not None:
                status = badge("warn", t("Behind"))
            else:
                status = badge("bad", t("Out of reach"))

            st.markdown(
                f'<div style="display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;">'
                f'<p class="card-title" style="font-size:1.2rem;">{goal["name"]}</p>{status}</div>'
                f'<p class="muted">{t("Target")}: {money(goal["amount"])} · '
                f'{t("Deadline")}: {goal["deadline_months"]} {t("months")} · '
                f'{t("With inflation")}: ~{money(real_target)}</p>',
                unsafe_allow_html=True
            )

            if goal["reached"]:
                st.success(f"✅ **{goal['name']}**: {t('reached in month')} {goal['month_reached']} ({t('target was month')} {goal['deadline_months']})")
            else:
                needed = results["required_monthly_per_goal"][goal["name"]]

                if actual_months is not None:
                    st.warning(
                        f"⚠️ **{goal['name']}**: {t('at your current savings trend, you would reach')} Rs {goal['amount']:,.0f} {t('in')} **{actual_months} {t('months')}** — "
                        f"{t('that is later than your')} {goal['deadline_months']}-{t('month target')}. "
                        f"{t('To hit your deadline, try saving')} Rs {needed:,.2f} {t('per month instead')}."
                    )
                else:
                    st.error(
                        f"🚨 **{goal['name']}**: {t('at your current rate, this goal is not reachable within 50 years.')} "
                        f"{t('You would need to save')} Rs {needed:,.2f} {t('per month to hit your')} {goal['deadline_months']}-{t('month target')}."
                    )

            # ====================================================
            # GAMIFICATION: progress bar, stage, milestone
            # ====================================================
            if allocation_item is not None:
                allocated_current_cents = allocation_item["suggested_current_allocation_cents"]
                allocated_monthly_cents = allocation_item["suggested_monthly_allocation_cents"]
                allocated_current = float(from_cents(allocated_current_cents))
                allocated_monthly = float(from_cents(allocated_monthly_cents))

                target_amount = float(goal["amount"])

                progress = calculate_goal_progress(allocated_current, target_amount)
                stage = get_goal_stage(allocated_current, target_amount)
                stage_name = get_stage_name(stage)
                current_milestone = get_current_milestone(allocated_current, target_amount)

                st.write("")
                st.markdown(
                    f'<p class="muted">{t("Stage")}: <strong>{t(stage_name)}</strong> · '
                    f'{t("Suggested savings allocated to this goal")}: {money(allocated_current)} '
                    f'({progress:.0f}%)</p>',
                    unsafe_allow_html=True
                )
                st.progress(min(max(progress / 100, 0.0), 1.0))

                # -------- milestone message (only fires once per new milestone reached) --------
                previous_milestone_key = f"previous_milestone_{goal['name']}"
                if previous_milestone_key not in st.session_state:
                    st.session_state[previous_milestone_key] = current_milestone

                previous_milestone = st.session_state[previous_milestone_key]
                new_milestone = check_for_new_milestone(previous_milestone, current_milestone)

                if current_milestone > previous_milestone:
                    st.session_state[previous_milestone_key] = current_milestone

                if new_milestone:
                    st.success(get_milestone_message(new_milestone))
                elif current_milestone > 0:
                    st.caption(get_milestone_message(current_milestone))

                # -------- projected completion at this allocated rate --------
                projected_months = calculate_projected_completion(
                    allocated_current_cents, to_cents(target_amount), allocated_monthly_cents
                )
                if projected_months is not None:
                    st.caption(
                        f"{t('At this suggested pace, you would reach this goal in about')} "
                        f"{projected_months} {t('months')}."
                    )

                # -------- personalised AI suggestion button --------
                ai_message_key = f"ai_goal_message_{goal['name']}"
                if st.button("✨ " + t("Get personalised suggestions"), key=f"ai_button_{i}"):
                    with st.spinner(t("Creating your personalised suggestions...")):
                        remaining_amount = max(target_amount - allocated_current, 0)
                        ai_message = generate_ai_financial_message(
                            goal_name=goal["name"],
                            current_savings=allocated_current,
                            target_amount=target_amount,
                            remaining_amount=remaining_amount,
                            progress=progress,
                            years=goal["deadline_months"] / 12
                        )
                        st.session_state[ai_message_key] = ai_message

                if ai_message_key in st.session_state:
                    st.info(st.session_state[ai_message_key])

            with st.expander(f"📈 {t('See')} {goal['name']} {t('vs. inflation-adjusted target')}"):
                deadline_months = goal["deadline_months"]

                # ALWAYS compute a fresh projection for exactly this goal's own
                # deadline length - do NOT slice the shared 60-month projection,
                # since goals longer than 60 months would mismatch lengths with
                # the inflating target line and corrupt the chart.
                fresh_projection = project_savings(
                    starting_balance=st.session_state["current_savings"],
                    monthly_contribution=st.session_state["monthly_savings"],
                    annual_rate=st.session_state["savings_rate"],
                    months=deadline_months
                )
                savings_for_this_goal = [m["balance"] for m in fresh_projection]

                # the inflating target line, guaranteed same length
                inflating_line = inflating_target_over_time(goal["amount"], deadline_months)

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=savings_for_this_goal, mode="lines", name=t("Your savings"), line=dict(width=3)
                ))
                fig.add_trace(go.Scatter(
                    y=inflating_line, mode="lines", name=t("Inflating target"), line=dict(width=3, dash="dash")
                ))
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10), height=320,
                    xaxis_title=t("Month"), yaxis_title=t("Rs"),
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(style_fig(fig), use_container_width=True, key=f"goal_chart_{i}")

        st.write("")
else:
    with st.container(key="card_nogoals"):
        st.info(t("You haven't added any goals yet — go to your Finances page to add one."))
        safe_link(FINANCES_PAGE, t("Add a goal"), ":material/add_circle:")

# ---------- AI explanation ----------
if goals_status:
    with st.container(key="card_explain"):
        st.markdown(f'<p class="card-title">{t("💡 Explain my results")}</p>', unsafe_allow_html=True)
        st.caption(t("Get a plain-language summary and what would change if you saved 10% more."))
        if st.button(t("💡 Explain my results")):
            with st.spinner(t("Thinking...")):
                adjusted_goals = simulate_savings_increase(st.session_state, increase_percent=0.10)
                explanation = explain_goals(
                    results["goals_status"],
                    adjusted_goals,
                    results["actual_months_per_goal"],
                    results["required_monthly_per_goal"],
                    st.session_state["monthly_savings"],
                    dict(st.session_state),
                    results["inflation_adjusted_target_per_goal"]
                )
            st.info(explanation)  # already in the right language via the AI prompt itself
