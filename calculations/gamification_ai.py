import os
import streamlit as st
from groq import Groq


def generate_ai_financial_message(
    goal_name,
    current_savings,
    target_amount,
    remaining_amount,
    progress,
    years
):
    """
    Generate personalised financial suggestions
    for a specific savings goal.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            api_key = None

    if not api_key:
        return (
            "AI suggestions are unavailable because "
            "the Groq API key has not been configured."
        )

    client = Groq(api_key=api_key)

    prompt = f"""
You are a friendly financial planning assistant
inside a savings goal simulator.

The user has a savings goal called:

Goal: {goal_name}

Their current financial information is:

Current savings: Rs {current_savings:,.2f}
Target amount: Rs {target_amount:,.2f}
Amount remaining: Rs {remaining_amount:,.2f}
Progress: {progress:.1f}%
Target timeframe: {years} years

Analyse this information and provide personalised,
practical suggestions that could help the user make
progress toward this specific goal.

Your response must:

- Briefly interpret the user's current progress.
- Mention the amount they still need to save.
- Give 2 or 3 realistic suggestions for progressing
  toward the goal.
- Suggestions may include increasing regular savings,
  reviewing unnecessary expenses, finding additional
  income, or redirecting occasional extra money toward
  the goal.
- Do not recommend taking loans or using risky investments
  simply to reach the goal faster.
- Do not shame the user.
- Do not make assumptions about their lifestyle.
- Keep the response concise enough to fit inside a
  dashboard card.
- Make the suggestions feel personalised to the numbers
  provided rather than generic financial advice.
- Do not mention milestones or milestone percentages.
- Do not ask the user to enter or adjust any information.
- End with a short encouraging sentence.

Use this structure:

A short observation about their progress.

💡 Suggestion 1

💡 Suggestion 2

💡 Suggestion 3

A short encouraging closing sentence.

Do not add a title because the application already
provides one.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a practical, concise and "
                        "friendly financial planning assistant."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=250
        )

        return response.choices[0].message.content

    except Exception:
        return (
            "I couldn't generate your personalised "
            "suggestions right now. Please try again."
        )