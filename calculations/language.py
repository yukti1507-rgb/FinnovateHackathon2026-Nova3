import streamlit as st
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

language_options = {"English": "en", "Français": "fr"}


@st.cache_data(show_spinner=False)
def translate_text(text, lang_name):
    if lang_name == "English":
        return text  # no need to call the API for English at all

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{
            "role": "user",
            "content": f"Translate this app UI text to {lang_name}. Keep any emojis and markdown formatting (like **bold**) exactly as they are. Reply with ONLY the translation, nothing else: '{text}'"
        }]
    )
    return response.choices[0].message.content.strip()


def t(text):
    lang = st.session_state.get("language", "en")
    lang_name = {"en": "English", "fr": "French"}.get(lang, "English")
    return translate_text(text, lang_name)


def show_language_picker():
    if "language" not in st.session_state:
        st.session_state["language"] = "en"

    with st.sidebar:
        choice = st.selectbox(
            "🌐 Language / Langue",
            options=list(language_options.keys()),
            index=list(language_options.values()).index(st.session_state["language"])
        )
        st.session_state["language"] = language_options[choice]