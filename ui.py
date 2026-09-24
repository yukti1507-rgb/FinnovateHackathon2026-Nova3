# ui.py - shared look & feel for every page
# (theme + display modes, navbar, cards, tiles, chart styling)

import os
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).parent          # your project folder (where Home.py is)

# ---------- Edit these to match your project ----------
APP_NAME = "GoalPath AI"
LOGO_PATH = "logo.png"          # <- put your existing logo file name here
CURRENCY = "Rs"

# ---------- Your real page files (these MUST match the files in pages/) ----------
HOME_PAGE      = "Home.py"
DASHBOARD_PAGE = "pages/Dashboard.py"
FINANCES_PAGE  = "pages/2_Your_Finances.py"     # income, expenses, loans, savings, goals
GOALS_PAGE     = "pages/3_Goals.py"             # goal results + AI explanation
FORECAST_PAGE  = "pages/4_finance_profile.py"   # spending / loan / goal charts
PROFILE_PAGE   = "pages/Profile.py"
ADMIN_PAGE     = "pages/Admin.py"

# If a page file isn't named exactly as above, look for it in pages/ by keyword,
# so links never show "coming soon" just because of a filename mismatch.
def _resolve(default, *keywords):
    if (BASE_DIR / default).exists():
        return default
    pages_dir = BASE_DIR / "pages"
    if pages_dir.is_dir():
        for f in sorted(pages_dir.glob("*.py")):
            if all(k in f.name.lower() for k in keywords):
                return f"pages/{f.name}"
    return default


DASHBOARD_PAGE = _resolve(DASHBOARD_PAGE, "dashboard")
FINANCES_PAGE  = _resolve(FINANCES_PAGE, "finances")
GOALS_PAGE     = _resolve(GOALS_PAGE, "goal")
FORECAST_PAGE  = _resolve(FORECAST_PAGE, "forecast")
LOANS_PAGE     = _resolve("pages/loans.py", "loan")

# links in the top navbar: (label, file, icon)
NAV_PAGES = [
    ("Dashboard",     DASHBOARD_PAGE, ":material/space_dashboard:"),
    ("Your Finances", FINANCES_PAGE,  ":material/account_balance_wallet:"),
    ("Loans",         LOANS_PAGE,     ":material/account_balance:"),
    ("Goals",         GOALS_PAGE,     ":material/flag:"),
    ("Forecast",      FORECAST_PAGE,  ":material/trending_up:"),
]

# big clickable blocks on the dashboard: (label, file, icon, short description)
TILE_PAGES = [
    ("Income",   FINANCES_PAGE, ":material/payments:",        "Add and track what you earn"),
    ("Loans",    LOANS_PAGE,    ":material/account_balance:", "Your loans and repayments"),
    ("Goals",    GOALS_PAGE,    ":material/flag:",            "See if you'll hit each goal"),
    ("Forecast", FORECAST_PAGE, ":material/trending_up:",     "See where your money is heading"),
]


# ======================================================================
# DISPLAY MODES
# Every colour on the site is a CSS variable (var(--text), var(--card)...).
# Each mode just gives those variables different values.
# ======================================================================
MODES = ["System default", "Light", "Dark", "Colour-blind friendly"]

PALETTES = {
    # your blue palette
    "Light": {
        "bg": "#F2F7FA", "card": "#FFFFFF", "text": "#001B48", "muted": "#5A6B82",
        "brand": "#001B48", "primary": "#02457A", "accent": "#018ABE", "soft": "#97CADB",
        "surface": "#D6E8EE", "border": "#D6E8EE", "input": "#FFFFFF",
        "pos": "#018ABE", "neg": "#001B48", "good": "#018ABE", "warn": "#B26A00", "bad": "#B42318",
    },
    # same blues, dark background
    "Dark": {
        "bg": "#061429", "card": "#0D1F3C", "text": "#E6F1F6", "muted": "#9AB2C8",
        "brand": "#001B48", "primary": "#1C6FB0", "accent": "#4DB8E6", "soft": "#97CADB",
        "surface": "#16335A", "border": "#1F3D66", "input": "#0A1A33",
        "pos": "#6CCBF2", "neg": "#E6F1F6", "good": "#6CCBF2", "warn": "#F2B84B", "bad": "#FF8A7A",
    },
    # Okabe-Ito colours: blue + orange stay distinguishable for all common
    # types of colour blindness (red/green, blue/yellow). Never green vs red.
    "Colour-blind friendly": {
        "bg": "#F7F9FB", "card": "#FFFFFF", "text": "#0B1F3A", "muted": "#3F4F63",
        "brand": "#003A63", "primary": "#0072B2", "accent": "#0072B2", "soft": "#56B4E9",
        "surface": "#E3F0F8", "border": "#9FB6C8", "input": "#FFFFFF",
        "pos": "#0072B2", "neg": "#D55E00", "good": "#0072B2", "warn": "#E69F00", "bad": "#D55E00",
    },
}

# chart line colours per mode
CHART_COLOURS = {
    "Light": ["#02457A", "#018ABE", "#97CADB", "#001B48", "#5A6B82"],
    "Dark":  ["#4DB8E6", "#97CADB", "#1C6FB0", "#E6F1F6", "#9AB2C8"],
    "Colour-blind friendly": ["#0072B2", "#E69F00", "#56B4E9", "#D55E00", "#009E73", "#CC79A7"],
}

# Colour names for inline HTML - they follow the chosen mode automatically
TEXT, MUTED, CARD = "var(--text)", "var(--muted)", "var(--card)"
BRAND, PRIMARY, ACCENT = "var(--brand)", "var(--primary)", "var(--accent)"
SOFT, SURFACE = "var(--soft)", "var(--surface)"
POS, NEG = "var(--pos)", "var(--neg)"
# old names, so older pages keep working
NAVY, DEEP, BLUE, SKY, MIST = BRAND, PRIMARY, ACCENT, SOFT, SURFACE


def current_mode():
    return st.session_state.get("display_mode", "System default")


def _vars(p):
    return "; ".join(f"--{k}: {v}" for k, v in p.items()) + ";"


def _save_mode():
    # the picker widget forgets its value when you change page,
    # so the choice is copied into a normal session_state key
    st.session_state["display_mode"] = st.session_state["_mode_picker"]


def display_settings():
    """The accessibility button (used in the navbar and on Home)."""
    with st.popover("Display", icon=":material/contrast:", help="Light, dark or colour-blind friendly"):
        st.radio(
            "Display mode",
            MODES,
            index=MODES.index(current_mode()),
            key="_mode_picker",
            on_change=_save_mode,
            captions=[
                "Follows your computer's setting",
                "Light background",
                "Dark background, easier at night",
                "Blue & orange instead of green & red, plus icons and patterns",
            ],
        )


def apply_theme():
    """Injects the global CSS. Call right after st.set_page_config on every page."""
    mode = current_mode()
    if mode == "System default":
        root = f":root {{ {_vars(PALETTES['Light'])} }}\n" \
               f"@media (prefers-color-scheme: dark) {{ :root {{ {_vars(PALETTES['Dark'])} }} }}"
    else:
        root = f":root {{ {_vars(PALETTES[mode])} }}"

    colour_blind_css = ""
    if mode == "Colour-blind friendly":
        colour_blind_css = """
/* links are underlined so they don't rely on colour */
.stApp a[data-testid="stPageLink-NavLink"] p { text-decoration: underline; text-underline-offset: 3px; }
[class*="st-key-tile_"] a p { text-decoration: none !important; }
/* thicker focus ring */
.stApp *:focus-visible { outline: 3px solid #E69F00 !important; outline-offset: 2px; }
/* thick left bar on messages - shape + icon, not just colour */
[data-testid="stAlertContainer"] { border-left: 6px solid var(--border); }
"""

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
{root}

html, body, [class*="css"], .stApp, button, input, textarea, select {{
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}}
.stApp {{ background: var(--bg); color: var(--text); }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp p, .stApp li, .stApp label {{ color: var(--text); }}
.stApp h1, .stApp h2, .stApp h3 {{ letter-spacing: -0.01em; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: var(--muted) !important; }}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] p {{ color: var(--text); }}
hr {{ border-color: var(--border) !important; }}

/* ---- remove the sidebar completely ---- */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarNav"] {{ display: none !important; }}

header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.2rem; max-width: 1280px; }}

/* ---- cards: any container with key starting "card_" ---- */
[class*="st-key-card_"] {{
    background: var(--card);
    border-radius: 20px;
    padding: 22px 24px;
    border: 1px solid var(--border);
}}
.card-title {{ font-weight: 700; font-size: 1rem; color: var(--text) !important; margin: 0 0 4px 0; }}
.muted {{ color: var(--muted) !important; font-size: 0.85rem; }}
.big-number {{ font-size: 1.9rem; font-weight: 800; color: var(--primary) !important; margin: 4px 0 0; }}

/* ---- status badge (icon + word, never colour alone) ---- */
.badge {{ display: inline-flex; align-items: center; gap: 6px; border-radius: 999px;
          padding: 4px 12px; font-size: .85rem; font-weight: 700; border: 2px solid currentColor; }}
.badge.good {{ color: var(--good) !important; }}
.badge.warn {{ color: var(--warn) !important; }}
.badge.bad  {{ color: var(--bad)  !important; }}

/* ---- navbar ---- */
.st-key-navbar {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 8px 16px;
    margin-bottom: 18px;
    position: sticky; top: 0.5rem; z-index: 99;
}}
.st-key-navbar [data-testid="stHorizontalBlock"] {{ align-items: center; }}
.st-key-navbar a[data-testid="stPageLink-NavLink"] {{
    border-radius: 12px; padding: 8px 12px; justify-content: center;
}}
.st-key-navbar a[data-testid="stPageLink-NavLink"]:hover {{ background: var(--surface); }}
.st-key-navbar a p {{ font-weight: 600; }}
.st-key-navbar [data-testid="stIconMaterial"] {{ color: var(--accent); }}
.st-key-nav_active a[data-testid="stPageLink-NavLink"] {{ background: var(--primary); }}
.st-key-nav_active a p, .st-key-nav_active [data-testid="stIconMaterial"] {{ color: #FFFFFF !important; }}
.brand {{ font-weight: 800; font-size: 1.25rem; color: var(--text); }}
.brand span {{ display:inline-grid; place-items:center; width:32px; height:32px;
    border-radius:10px; background: var(--primary); color:#fff !important; margin-right:8px; font-size:0.95rem; }}

/* ---- icon tiles (whole block is clickable) ---- */
[class*="st-key-tile_"] {{
    position: relative;
    background: var(--card);
    border-radius: 20px;
    padding: 18px 20px 14px 20px;
    border: 1px solid var(--border);
    transition: border-color .15s, transform .15s;
}}
[class*="st-key-tile_"]:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
[class*="st-key-tile_"] a[data-testid="stPageLink-NavLink"] {{
    flex-direction: column; align-items: flex-start; gap: 10px; padding: 0; background: none;
}}
[class*="st-key-tile_"] a[data-testid="stPageLink-NavLink"]::after {{ content: ""; position: absolute; inset: 0; }}
[class*="st-key-tile_"] [data-testid="stIconMaterial"] {{
    font-size: 1.8rem; color: var(--accent); background: var(--surface); border-radius: 14px; padding: 10px;
}}
[class*="st-key-tile_"] a p {{ font-weight: 700; font-size: 1.05rem; }}

/* ---- quick-action buttons ---- */
.st-key-quick a[data-testid="stPageLink-NavLink"] {{
    flex-direction: column; gap: 4px; background: var(--bg); border-radius: 14px; padding: 12px 6px;
}}
.st-key-quick a p {{ font-size: 0.8rem; font-weight: 600; }}
.st-key-quick [data-testid="stIconMaterial"] {{ color: var(--primary); }}

/* ---- buttons ---- */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button,
[data-testid="stPopoverButton"] {{
    background: var(--primary); color: #FFFFFF; border: none; border-radius: 12px;
    font-weight: 600; padding: 0.5rem 1.1rem;
}}
.stButton > button p, .stFormSubmitButton > button p, .stDownloadButton > button p,
[data-testid="stPopoverButton"] p, [data-testid="stPopoverButton"] span {{ color: #FFFFFF !important; }}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover,
[data-testid="stPopoverButton"]:hover {{ background: var(--accent); color: #FFFFFF; }}
.stApp *:focus-visible {{ outline: 3px solid var(--soft); outline-offset: 2px; }}

/* ---- inputs, dropdowns, expanders, tabs, messages ---- */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
[data-baseweb="select"] > div {{
    background: var(--input) !important; border-color: var(--border) !important; border-radius: 12px !important;
}}
.stApp input, .stApp textarea {{ color: var(--text) !important; -webkit-text-fill-color: var(--text); background: transparent !important; }}
[data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] {{ background: var(--surface) !important; }}
[data-baseweb="popover"] ul, [data-baseweb="menu"], [role="listbox"] {{ background: var(--card) !important; }}
[role="option"], [role="option"] * {{ color: var(--text) !important; }}
[data-testid="stPopoverBody"] {{ background: var(--card) !important; border: 1px solid var(--border); }}
[data-testid="stExpander"] details {{ background: var(--card); border-radius: 14px; border: 1px solid var(--border); }}
[data-testid="stExpander"] summary:hover p {{ color: var(--accent) !important; }}
[data-baseweb="tab"] p {{ color: var(--text); }}
[data-testid="stAlertContainer"] p, [data-testid="stAlertContainer"] strong {{ color: var(--text) !important; }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {{ background: color-mix(in srgb, var(--good) 14%, transparent); border-color: var(--good); }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{ background: color-mix(in srgb, var(--warn) 16%, transparent); border-color: var(--warn); }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"])   {{ background: color-mix(in srgb, var(--bad) 14%, transparent);  border-color: var(--bad); }}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"])    {{ background: color-mix(in srgb, var(--soft) 22%, transparent); border-color: var(--soft); }}

/* ---- page header ---- */
.page-header h1 {{ margin: 0; font-size: 1.9rem; font-weight: 800; }}
.page-header p {{ margin: 4px 0 0 0; color: var(--muted) !important; }}

{colour_blind_css}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
""", unsafe_allow_html=True)


# ======================================================================
# CHARTS (plotly) - follow the chosen mode
# ======================================================================
def chart_colours():
    mode = current_mode()
    return CHART_COLOURS.get(mode, CHART_COLOURS["Light"])


def style_fig(fig):
    """Makes a plotly chart match the theme. Use: st.plotly_chart(style_fig(fig))"""
    mode = current_mode()
    font = {"Light": "#001B48", "Dark": "#E6F1F6", "Colour-blind friendly": "#0B1F3A"}.get(mode, "#6B7C93")
    colours = chart_colours()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color=font),
        colorway=colours, piecolorway=colours,
        legend=dict(font=dict(color=font)),
    )
    fig.update_xaxes(gridcolor="rgba(127,145,170,0.25)", zerolinecolor="rgba(127,145,170,0.35)")
    fig.update_yaxes(gridcolor="rgba(127,145,170,0.25)", zerolinecolor="rgba(127,145,170,0.35)")

    if mode == "Colour-blind friendly":
        # every line gets its own pattern + marker shape, so colour isn't needed
        dashes = ["solid", "dash", "dot", "dashdot"]
        symbols = ["circle", "square", "diamond", "triangle-up"]
        i = 0
        for trace in fig.data:
            if trace.type == "scatter":
                trace.update(line=dict(dash=dashes[i % 4]), marker=dict(symbol=symbols[i % 4], size=6),
                             mode="lines+markers")
                i += 1
            elif trace.type == "pie":
                trace.update(textinfo="label+percent",
                             marker=dict(line=dict(color="#FFFFFF", width=2)))
    return fig


# ======================================================================
# LAYOUT HELPERS
# ======================================================================
def show_logo(width=130):
    """Your logo if the file exists, otherwise a text logo."""
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=width)
    else:
        st.markdown(f'<div class="brand"><span>G</span>{APP_NAME}</div>', unsafe_allow_html=True)


def safe_link(path, label, icon=None):
    """Page link that shows 'coming soon' instead of crashing if the file doesn't exist."""
    if (BASE_DIR / path).exists():
        st.page_link(path, label=label, icon=icon)
    else:
        st.caption(f"{icon or ''} {label} (coming soon)")


def navbar(active=""):
    """Top navigation bar. `active` = label of the current page (e.g. "Goals")."""
    links = list(NAV_PAGES)
    if st.session_state.get("Admin"):                  # admins also get the Admin page
        links.append(("Admin", ADMIN_PAGE, ":material/admin_panel_settings:"))

    with st.container(key="navbar"):
        cols = st.columns([1.8] + [1.25] * len(links) + [1.1, 1.3])
        with cols[0]:
            show_logo(width=110)
        for col, (label, path, icon) in zip(cols[1:-2], links):
            with col:
                key = "nav_active" if label == active else f"nav_{label.lower().replace(' ', '_')}"
                with st.container(key=key):
                    safe_link(path, label, icon)
        with cols[-2]:
            display_settings()
        with cols[-1]:
            key = "nav_active" if active == "Profile" else "nav_profile"
            with st.container(key=key):
                safe_link(PROFILE_PAGE, st.session_state.get("username") or "Profile",
                          ":material/account_circle:")


def require_login():
    """Same login check your profile page used - stops the page if not logged in."""
    if not st.session_state.get("Logged_in") or not st.session_state.get("username"):
        st.warning("Please log in to access this page.")
        if st.button("Go to login page"):
            st.switch_page(HOME_PAGE)
        st.stop()


def require_admin():
    """Only admins get past this line."""
    require_login()
    if not st.session_state.get("Admin"):
        st.error("This page is only for administrators.")
        st.stop()


def status_colors():
    """(background, text) colours for the Admin audit table - follow the mode."""
    mode = current_mode()
    if mode == "Dark":
        return {"good": ("#123A55", "#6CCBF2"), "warn": ("#3D2E0B", "#F2B84B"), "bad": ("#46201C", "#FF8A7A")}
    if mode == "Colour-blind friendly":
        return {"good": ("#D6EAF5", "#004B75"), "warn": ("#FCEBC4", "#6B4A00"), "bad": ("#F8D9C4", "#8A3C00")}
    return {"good": ("#DDF1F7", "#02457A"), "warn": ("#FFF1D6", "#8A5A00"), "bad": ("#FBE0E0", "#9B1C1C")}


def page_header(title, subtitle=""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="page-header"><h1>{title}</h1>{sub}</div>', unsafe_allow_html=True)


def tile(label, path, icon, blurb, key):
    """A card-sized block that acts as a button to another page."""
    with st.container(key=f"tile_{key}"):
        safe_link(path, label, icon)
        st.caption(blurb)


def stat_card(key, label, value, note=""):
    """Small card with a label and a big number."""
    with st.container(key=f"card_{key}"):
        st.markdown(f'<p class="muted">{label}</p><p class="big-number">{value}</p>'
                    + (f'<p class="muted">{note}</p>' if note else ""), unsafe_allow_html=True)


def badge(kind, text):
    """kind = 'good' | 'warn' | 'bad'. Always shows an icon + word, not just a colour."""
    icon = {"good": "✔", "warn": "▲", "bad": "✖"}[kind]
    return f'<span class="badge {kind}">{icon} {text}</span>'


def money(x):
    return f"{CURRENCY} {x:,.0f}"