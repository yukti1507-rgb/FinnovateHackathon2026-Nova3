"""
Shared look & feel for every page (top navigation bar, theme modes, colour-blind mode).

Usage on every page, right after st.set_page_config(...):

    from app_model.ui_theme import apply_theme, render_navbar, page_header
    apply_theme()
    render_navbar()

Nothing in here changes what a page does - it only changes how it looks.
"""
from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from app_model.db import get_connection

ROOT = Path(__file__).resolve().parent.parent      # folder that contains Home.py and pages/
PAGES_DIR = ROOT / "pages"

MODES = ["System", "Light", "Dark"]                # "System" = follow the phone / computer setting
MODE_LABELS = {"System": "System default", "Light": "Light", "Dark": "Dark"}


# ----------------------------------------------------------------------------
# 1. Which pages appear in the navigation bar
# ----------------------------------------------------------------------------
# filename (lower-case) -> (label, icon).  Any page in pages/ that is NOT listed here
# is still added automatically (label taken from the filename), so nothing becomes unreachable.
KNOWN_PAGES = {
    "1_profile.py":           ("Profile",   ":material/person:"),
    "2_your_finances.py":     ("Finances",  ":material/account_balance_wallet:"),
    "3_dashboard.py":         ("Dashboard", ":material/dashboard:"),
    "4_loans.py":             ("Loans",     ":material/account_balance:"),
    "4_finance_profile.py":   ("Insights",  ":material/monitoring:"),
    "5_finance_yukti_py.py":  ("Planner",   ":material/savings:"),
    "admin.py":               ("Admin",     ":material/admin_panel_settings:"),
}
ADMIN_ONLY = {"admin.py"}          # these pages are never shown to non-admin users


def is_admin() -> bool:
    """True only for a logged-in user whose role in the database is 'Admin'."""
    ss = st.session_state
    if not ss.get("Logged_in") or not ss.get("username"):
        return False
    try:
        from app_model.users import get_role
        return get_role(get_connection(), ss["username"]) == "Admin"
    except Exception:
        return False


def require_admin() -> None:
    """Put this at the top of Admin.py: blocks the page for everyone except admins."""
    if not is_admin():
        st.error("You don't have permission to view this page.")
        st.stop()


def _label_from_filename(name: str) -> str:
    stem = re.sub(r"^\d+[_\-\s]*", "", Path(name).stem)
    return stem.replace("_", " ").strip().title() or name


def _sort_key(name: str):
    m = re.match(r"^(\d+)", name)
    return (0, int(m.group(1)), name.lower()) if m else (1, 0, name.lower())


def _nav_items():
    """[(path, label, icon)] for the current visitor."""
    ss = st.session_state
    logged_in = bool(ss.get("Logged_in") and ss.get("username"))

    if not logged_in:
        return [("Home.py", "Login", ":material/login:")] if (ROOT / "Home.py").exists() else []

    admin = is_admin()
    items = []
    files = sorted((p.name for p in PAGES_DIR.glob("*.py")), key=_sort_key) if PAGES_DIR.exists() else []
    for name in files:
        low = name.lower()
        if low in ADMIN_ONLY and not admin:
            continue
        label, icon = KNOWN_PAGES.get(low, (_label_from_filename(name), ":material/apps:"))
        items.append((f"pages/{name}", label, icon))
    return items


# ----------------------------------------------------------------------------
# 2. Saved appearance preferences (stored in user_profile.background_color)
# ----------------------------------------------------------------------------
def _decode(value):
    if not value:
        return None
    parts = str(value).split("|")
    if parts[0] not in MODES:
        return None
    return parts[0], ("Colorblind" in parts[1:])


def _encode(mode: str, cb: bool) -> str:
    return mode + ("|Colorblind" if cb else "")


def _saved_prefs(username: str):
    try:
        cur = get_connection().cursor()
        cur.execute(
            "SELECT p.background_color FROM user_profile p "
            "JOIN users_login u ON p.user_id = u.id WHERE u.username = ?",
            (username,),
        )
        row = cur.fetchone()
        return _decode(row[0]) if row else None
    except Exception:
        return None


def _save_prefs() -> None:
    ss = st.session_state
    if ss.get("Logged_in") and ss.get("username"):
        try:
            from app_model.users import update_background
            update_background(get_connection(), ss["username"], _encode(ss["theme_mode"], ss["theme_cb"]))
        except Exception:
            pass


def _reset_widget_state() -> None:
    for k in [k for k in st.session_state if str(k).startswith("_w_theme_")]:
        st.session_state.pop(k, None)


def _init_prefs() -> None:
    ss = st.session_state
    ss.setdefault("theme_mode", "System")          # default = follow the device
    ss.setdefault("theme_cb", False)

    user = ss.get("username") if ss.get("Logged_in") else None
    if user and ss.get("_prefs_user") != user:     # just logged in -> load their saved choice (if any)
        saved = _saved_prefs(user)
        if saved:
            ss["theme_mode"], ss["theme_cb"] = saved
            _reset_widget_state()
        ss["_prefs_user"] = user
    elif not user and ss.get("_prefs_user"):       # logged out -> back to the default
        ss["theme_mode"], ss["theme_cb"] = "System", False
        ss.pop("_prefs_user", None)
        _reset_widget_state()


def appearance_controls(key: str = "appearance") -> None:
    """Theme radio + colour-blind switch. Can be shown in several places (use a different key each time)."""
    ss = st.session_state
    _init_prefs()
    mode_key, cb_key = f"_w_theme_mode_{key}", f"_w_theme_cb_{key}"

    def _sync():
        ss["theme_mode"] = ss[mode_key]
        ss["theme_cb"] = ss[cb_key]
        _save_prefs()

    st.radio(
        "Theme",
        MODES,
        index=MODES.index(ss["theme_mode"]),
        format_func=lambda m: MODE_LABELS[m],
        captions=["Matches your phone or computer", "", ""],
        key=mode_key,
        on_change=_sync,
    )
    st.toggle(
        "Color-blind friendly",
        value=ss["theme_cb"],
        key=cb_key,
        on_change=_sync,
        help="Blue and orange instead of red and green, plus symbols so meaning never depends on color alone. "
             "Works with every theme above.",
    )


# ----------------------------------------------------------------------------
# 3. Colours
# ----------------------------------------------------------------------------
_LIGHT = dict(
    bg="#F2F5F9", surface="#FFFFFF", surface2="#EAF0F6", input_bg="#FFFFFF", nav_bg="#FFFFFF",
    border="rgba(15,23,42,.13)", text="#0F172A", muted="#475569", grid="rgba(15,23,42,.12)",
    glow="rgba(8,145,178,.10)", glow2="rgba(124,58,237,.07)", hero_a="#0E5468", hero_b="#0B2A3A",
    shadow="0 6px 20px rgba(15,23,42,.08)",
)
_DARK = dict(
    bg="#0A0E14", surface="#121A26", surface2="#182233", input_bg="#0E1622", nav_bg="#0B1118",
    border="rgba(255,255,255,.11)", text="#E8EEF6", muted="#A3B3C6", grid="rgba(255,255,255,.10)",
    glow="rgba(34,211,238,.11)", glow2="rgba(139,92,246,.10)", hero_a="#0B3A47", hero_b="#08121B",
    shadow="0 8px 24px rgba(0,0,0,.45)",
)

# accent + status colours + gradient tiles + navigation icon colours
_DEFAULT = {
    "light": dict(accent="#0E7490", on_accent="#FFFFFF", ok="#15803D", warn="#B45309", err="#B91C1C", info="#0369A1",
                  ic1="#C2410C", ic2="#6D28D9", ic3="#15803D"),
    "dark":  dict(accent="#22D3EE", on_accent="#03212A", ok="#34D399", warn="#FBBF24", err="#F87171", info="#38BDF8",
                  ic1="#FB923C", ic2="#A78BFA", ic3="#4ADE80"),
}
_CB = {   # Okabe-Ito colour-blind-safe palette
    "light": dict(accent="#0072B2", on_accent="#FFFFFF", ok="#0072B2", warn="#8A6D00", err="#B84C00", info="#8E3F6E",
                  ic1="#B45F00", ic2="#0072B2", ic3="#8E3F6E"),
    "dark":  dict(accent="#56B4E9", on_accent="#03202E", ok="#56B4E9", warn="#F0E442", err="#F08A3C", info="#CC79A7",
                  ic1="#E69F00", ic2="#56B4E9", ic3="#CC79A7"),
}
_TILES = [("#7C3AED", "#4C1D95"), ("#0891B2", "#0E5F73"), ("#2F6FEB", "#1E40AF"),
          ("#DB2777", "#9D174D"), ("#EA580C", "#9A3412"), ("#15803D", "#14532D")]
_TILES_CB = [("#0072B2", "#004E7C"), ("#B84C00", "#7A3200"), ("#00795A", "#004D39"),
             ("#A64B7C", "#6E2D52"), ("#3B4A63", "#1E293B"), ("#8A6D00", "#5C4900")]

COLORWAY = ["#22D3EE", "#A78BFA", "#F472B6", "#FBBF24", "#34D399", "#60A5FA", "#FB923C"]
COLORWAY_CB = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#F0E442"]


def status_colors() -> dict:
    """Background/text colours for the audit-log table (safe for colour-blind users when that mode is on)."""
    if st.session_state.get("theme_cb"):
        return {"bad": ("#FBE3D0", "#7A3200"), "warn": ("#FBF2C4", "#5C4900"), "good": ("#D6E9F8", "#004E7C")}
    return {"bad": ("#FDE2E2", "#B42318"), "warn": ("#FEF0C7", "#B54708"), "good": ("#DCFAE6", "#067647")}


def style_fig(fig):
    """Make a Plotly figure follow the current palette. Returns the figure."""
    cb = bool(st.session_state.get("theme_cb"))
    fig.update_layout(
        colorway=COLORWAY_CB if cb else COLORWAY,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    if cb:   # different line styles too, so lines can be told apart without colour
        dashes = ["solid", "dash", "dot", "dashdot"]
        for i, tr in enumerate(fig.data):
            if getattr(tr, "mode", None) and "lines" in str(tr.mode):
                tr.line.dash = tr.line.dash or dashes[i % len(dashes)]
    return fig


def _var_block(mode: str, cb: bool) -> str:
    base = dict(_DARK if mode == "dark" else _LIGHT)
    base.update((_CB if cb else _DEFAULT)[mode])
    css = [f"--{k.replace('_', '-')}:{v};" for k, v in base.items()]
    for i, (a, b) in enumerate(_TILES_CB if cb else _TILES, start=1):
        css.append(f"--t{i}a:{a};--t{i}b:{b};")
    return "".join(css)


def _theme_vars(mode: str, cb: bool) -> str:
    if mode == "Light":
        return f":root{{color-scheme:light;{_var_block('light', cb)}}}"
    if mode == "Dark":
        return f":root{{color-scheme:dark;{_var_block('dark', cb)}}}"
    return (f":root{{color-scheme:light dark;{_var_block('light', cb)}}}"
            f"@media (prefers-color-scheme: dark){{:root{{{_var_block('dark', cb)}}}}}")


def _mismatch_css(mode: str) -> str:
    """Streamlit draws tables on a canvas using the *device* theme. If the person forces the opposite
    theme, flip the table so it still matches."""
    if mode == "Dark":
        media = "light"
    elif mode == "Light":
        media = "dark"
    else:
        return ""
    return (f"@media (prefers-color-scheme: {media}){{"
            "[data-testid='stDataFrame']{filter:invert(.92) hue-rotate(180deg);}}")


def _alert_css() -> str:
    out = []
    for kind, var in (("Info", "info"), ("Success", "ok"), ("Warning", "warn"), ("Error", "err")):
        sel = f'[data-testid="stAlert"]:has([data-testid="stAlertContent{kind}"])'
        out.append(
            f"{sel},{sel}>div{{background:color-mix(in srgb,var(--{var}) 15%,var(--surface)) !important;"
            f"border-color:var(--{var}) !important;}}"
        )
    return "".join(out)


# ----------------------------------------------------------------------------
# 4. The stylesheet
# ----------------------------------------------------------------------------
_STATIC_CSS = """
html,body,.stApp{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;}
.stApp{background-color:var(--bg);
  background-image:radial-gradient(900px 420px at 92% -8%,var(--glow),transparent 65%),
                   radial-gradient(700px 380px at -6% 108%,var(--glow2),transparent 60%);
  background-attachment:fixed;color:var(--text);}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stMainBlockContainer"],.block-container{padding-top:3.6rem !important;max-width:1320px;}
[data-testid="stElementContainer"]:has(style){display:none;}
[data-testid="stSidebarNav"]{display:none !important;}
[data-testid="stSidebar"]{background:var(--nav-bg);border-right:1px solid var(--border);}
hr{border-color:var(--border) !important;}

/* ---- text ---- */
.stApp h1{font-family:'Orbitron','Inter',sans-serif;}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{color:var(--text) !important;}
.stApp p,.stApp li,.stApp label,.stApp [data-testid="stWidgetLabel"]{color:var(--text);}
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] p,.stApp small{color:var(--muted) !important;}
.stApp [data-testid="stMarkdownContainer"] a{color:var(--accent);}
.fm-accent{color:var(--accent) !important;}
.stApp *:focus-visible{outline:3px solid var(--accent) !important;outline-offset:2px;}

/* ---- inputs ---- */
.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"],.stApp [data-baseweb="textarea"],
.stApp [data-baseweb="select"]>div{background:var(--input-bg) !important;border-color:var(--border) !important;
  border-radius:12px !important;}
.stApp input,.stApp textarea{color:var(--text) !important;-webkit-text-fill-color:var(--text) !important;
  background:transparent !important;}
.stApp input::placeholder,.stApp textarea::placeholder{color:var(--muted) !important;
  -webkit-text-fill-color:var(--muted) !important;opacity:.85;}
.stApp [data-baseweb="select"] *{color:var(--text);}
.stApp [data-baseweb="select"] svg{fill:var(--muted) !important;}
.stApp [data-testid="stNumberInputStepUp"],.stApp [data-testid="stNumberInputStepDown"]{background:var(--surface2) !important;color:var(--text) !important;}
[data-baseweb="popover"] [data-baseweb="menu"],[data-baseweb="popover"]>div,ul[role="listbox"]{background:var(--surface) !important;color:var(--text) !important;}
li[role="option"]{color:var(--text) !important;}
li[role="option"]:hover,li[role="option"][aria-selected="true"]{background:var(--surface2) !important;}
.stApp [data-testid="stSlider"] *{color:var(--text);}
.stApp [data-testid="stFileUploaderDropzone"]{background:var(--surface2);border:1px dashed var(--border);border-radius:14px;}
.stApp [data-testid="stFileUploaderDropzone"] *{color:var(--text);}
[data-testid="stPopoverBody"]{background:var(--surface) !important;border:1px solid var(--border) !important;border-radius:16px !important;}

/* ---- buttons: outlined by default, filled for primary and form submit ---- */
.stApp [data-testid^="stBaseButton-"]{border-radius:12px;font-weight:600;transition:background .15s,box-shadow .15s;}
.stApp [data-testid="stBaseButton-secondary"]{background:transparent;color:var(--accent);border:1.5px solid var(--accent);}
.stApp [data-testid="stBaseButton-secondary"]:hover{background:color-mix(in srgb,var(--accent) 14%,transparent);color:var(--accent);border-color:var(--accent);}
.stApp [data-testid^="stBaseButton-primary"],.stApp [data-testid="stBaseButton-secondaryFormSubmit"]{background:var(--accent);color:var(--on-accent);border:1.5px solid var(--accent);}
.stApp [data-testid^="stBaseButton-primary"]:hover,.stApp [data-testid="stBaseButton-secondaryFormSubmit"]:hover{filter:brightness(1.08);color:var(--on-accent);border-color:var(--accent);}
.stApp [data-testid^="stBaseButton-"] p{color:inherit !important;}

/* ---- cards ---- */
.stApp [data-testid="stForm"]{background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:1.2rem;box-shadow:var(--shadow);}
.stApp [data-testid="stExpander"]{background:var(--surface);border:1px solid var(--border) !important;border-radius:16px;overflow:hidden;}
.stApp [data-testid="stExpander"] summary{color:var(--text);font-weight:600;}
.stApp [data-testid="stExpander"] summary p{color:var(--text);}
.stApp [data-testid="stPlotlyChart"]{background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:.6rem;box-shadow:var(--shadow);}
.stApp [data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:14px;overflow:hidden;}
.stApp [data-testid="stTable"] table{background:var(--surface);}
.stApp [data-testid="stTable"] th,.stApp [data-testid="stTable"] td{color:var(--text) !important;border-color:var(--border) !important;}
.stApp [data-testid="stChatMessage"]{background:var(--surface);border:1px solid var(--border);border-radius:16px;}
.stApp [data-testid="stChatInput"]{background:var(--input-bg);border-radius:14px;}
.js-plotly-plot .xtick text,.js-plotly-plot .ytick text,.js-plotly-plot .legendtext,.js-plotly-plot .gtitle,
.js-plotly-plot .g-xtitle text,.js-plotly-plot .g-ytitle text,.js-plotly-plot .annotation-text{fill:var(--text) !important;}
.js-plotly-plot .gridlayer path,.js-plotly-plot .zerolinelayer path{stroke:var(--grid) !important;}

/* ---- tabs ---- */
.stApp [data-baseweb="tab-list"]{gap:6px;}
.stApp button[data-baseweb="tab"]{font-weight:600;padding:10px 18px;color:var(--muted);}
.stApp button[data-baseweb="tab"] p{color:inherit !important;font-weight:600;}
.stApp button[data-baseweb="tab"][aria-selected="true"]{color:var(--accent);}
.stApp [data-baseweb="tab-highlight"]{background-color:var(--accent) !important;height:3px;}
.stApp [data-baseweb="tab-border"]{background-color:var(--border) !important;}

/* ---- alerts ---- */
.stApp [data-testid="stAlert"]{border:1px solid var(--border);border-left-width:6px;border-radius:14px;}
.stApp [data-testid="stAlert"] *{color:var(--text) !important;}

/* ---- metrics become gradient tiles (like the category blocks) ---- */
.stApp [data-testid="stMetric"]{position:relative;overflow:hidden;padding:20px 22px !important;border-radius:20px;
  background:linear-gradient(145deg,var(--t1a),var(--t1b));border:1px solid rgba(255,255,255,.16);box-shadow:var(--shadow);}
.stApp [data-testid="stMetric"]::after{content:"\\2022  \\2022  \\2022";position:absolute;top:8px;right:16px;font-size:13px;color:rgba(255,255,255,.7);}
.stApp [data-testid="stMetric"] *{color:#fff !important;}
.stApp [data-testid="stMetricLabel"] p{font-weight:600;opacity:.92;}
.stApp [data-testid="stMetricValue"]{font-weight:800;}
.stApp [data-testid="stColumn"]:nth-child(6n+2) [data-testid="stMetric"]{background:linear-gradient(145deg,var(--t2a),var(--t2b));}
.stApp [data-testid="stColumn"]:nth-child(6n+3) [data-testid="stMetric"]{background:linear-gradient(145deg,var(--t3a),var(--t3b));}
.stApp [data-testid="stColumn"]:nth-child(6n+4) [data-testid="stMetric"]{background:linear-gradient(145deg,var(--t4a),var(--t4b));}
.stApp [data-testid="stColumn"]:nth-child(6n+5) [data-testid="stMetric"]{background:linear-gradient(145deg,var(--t5a),var(--t5b));}
.stApp [data-testid="stColumn"]:nth-child(6n+6) [data-testid="stMetric"]{background:linear-gradient(145deg,var(--t6a),var(--t6b));}

/* ---- page header (existing pages already use class finance-header) ---- */
.finance-header{position:relative;overflow:hidden;border-radius:22px;padding:30px 34px;margin-bottom:24px;
  border:1px solid rgba(255,255,255,.12);
  background:radial-gradient(520px 200px at 88% 0%,rgba(34,211,238,.32),transparent 70%),
             linear-gradient(135deg,var(--hero-a),var(--hero-b));box-shadow:var(--shadow);}
.finance-header::before{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:34px 34px;}
.finance-header h1,.finance-header p{position:relative;}
.finance-header h1{margin:0;padding:0 !important;font-size:1.9rem !important;font-weight:800;letter-spacing:.02em;color:#fff !important;}
.finance-header p{margin:8px 0 0;font-size:1rem;color:rgba(255,255,255,.8) !important;}

/* ---- blink-style tiles + banner (used on the login page) ---- */
.fm-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;margin:4px 0 20px;}
.fm-tile{border-radius:20px;padding:14px 14px 18px;text-align:center;color:#fff;box-shadow:var(--shadow);
  border:1px solid rgba(255,255,255,.14);background:linear-gradient(145deg,var(--t1a),var(--t1b));}
.fm-tile:nth-child(2){background:linear-gradient(145deg,var(--t2a),var(--t2b));}
.fm-tile:nth-child(3){background:linear-gradient(145deg,var(--t3a),var(--t3b));}
.fm-tile:nth-child(4){background:linear-gradient(145deg,var(--t4a),var(--t4b));}
.fm-tile:nth-child(5){background:linear-gradient(145deg,var(--t5a),var(--t5b));}
.fm-tile .dots{font-size:12px;letter-spacing:3px;color:rgba(255,255,255,.7);}
.fm-tile .ico{display:flex;align-items:center;justify-content:center;height:62px;margin:8px auto 12px;border-radius:999px;
  background:rgba(255,255,255,.15);font-size:1.8rem;}
.fm-tile b{display:block;font-size:.85rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#fff;}
.fm-tile span.sub{display:block;margin-top:4px;font-size:.8rem;color:rgba(255,255,255,.88);}
.fm-banner{position:relative;overflow:hidden;border-radius:26px;padding:30px 34px;margin:4px 0 20px;color:#fff;
  background:linear-gradient(120deg,var(--t1a),var(--t4a));box-shadow:var(--shadow);}
.fm-banner::before{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(255,255,255,.07) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(255,255,255,.07) 1px,transparent 1px);background-size:56px 56px;}
.fm-banner h2{position:relative;margin:0 0 8px;font-family:'Orbitron','Inter',sans-serif;font-size:1.5rem;letter-spacing:.04em;color:#fff !important;
  display:inline-block;padding-bottom:8px;border-bottom:3px solid #fff;}
.fm-banner p{position:relative;margin:6px 0 0;color:rgba(255,255,255,.92) !important;}

/* ---- top navigation bar ---- */
.st-key-topnav{background:var(--nav-bg);border:1px solid var(--border);border-radius:20px;padding:6px 16px;
  margin-bottom:22px;box-shadow:var(--shadow);}
.st-key-topnav [data-testid="stHorizontalBlock"]{align-items:center;flex-wrap:nowrap !important;gap:.25rem;}
.st-key-topnav [data-testid="stColumn"]{min-width:0 !important;}
.fm-brand{display:flex;align-items:center;gap:10px;white-space:nowrap;}
.fm-brand svg{flex:none;}
.fm-brand b{font-family:'Orbitron','Inter',sans-serif;font-size:1.3rem;font-weight:800;color:var(--accent);letter-spacing:.02em;}
.fm-brand small{font-family:'Orbitron','Inter',sans-serif;font-size:.6rem;letter-spacing:.16em;color:var(--muted);text-transform:uppercase;}
.st-key-topnav a[data-testid="stPageLink-NavLink"],
.st-key-topnav [data-testid="stPopover"] button{flex-direction:column;justify-content:center;align-items:center;gap:2px;
  padding:8px 6px;border-radius:14px;text-align:center;line-height:1.1;width:100%;background:transparent !important;
  border:none !important;color:var(--text) !important;text-decoration:none;}
.st-key-topnav [data-testid="stPopover"] button>div{flex-direction:column;align-items:center;gap:2px;}
.st-key-topnav a[data-testid="stPageLink-NavLink"] p,.st-key-topnav [data-testid="stPopover"] button p{
  font-size:.78rem;font-weight:600;margin:0;color:inherit !important;}
.st-key-topnav [data-testid^="stIcon"]{font-size:1.6rem !important;}
.st-key-topnav [data-testid="stColumn"]:nth-child(3n+2) [data-testid^="stIcon"]{color:var(--ic1);}
.st-key-topnav [data-testid="stColumn"]:nth-child(3n+3) [data-testid^="stIcon"]{color:var(--ic2);}
.st-key-topnav [data-testid="stColumn"]:nth-child(3n+4) [data-testid^="stIcon"]{color:var(--ic3);}
.st-key-topnav a[data-testid="stPageLink-NavLink"]:hover,.st-key-topnav [data-testid="stPopover"] button:hover{
  background:color-mix(in srgb,var(--accent) 14%,transparent) !important;}
.st-key-topnav a[aria-current="page"]{background:color-mix(in srgb,var(--accent) 16%,transparent) !important;
  box-shadow:inset 0 -3px 0 var(--accent);}
@media (max-width:820px){.st-key-topnav a[data-testid="stPageLink-NavLink"] p,.fm-brand small{display:none;}}

@media (prefers-reduced-motion:reduce){*{transition:none !important;animation:none !important;}}
"""

_CB_EXTRA = """
.stApp [data-testid="stMarkdownContainer"] a{text-decoration:underline;}
.stApp [data-testid="stAlert"]{border-left-width:10px;}
"""

_LOGO = (
    '<svg width="34" height="34" viewBox="0 0 32 32" aria-hidden="true">'
    '<path d="M18.5 2 6 18h8l-2 12L26 13h-8z" fill="var(--accent)"/></svg>'
)


def apply_theme() -> None:
    """Inject the shared stylesheet. Call once per page, straight after st.set_page_config()."""
    _init_prefs()
    mode = st.session_state["theme_mode"]
    cb = bool(st.session_state["theme_cb"])
    css = (
        "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800"
        "&family=Orbitron:wght@600;700;800&display=swap');"
        + _theme_vars(mode, cb)
        + _STATIC_CSS
        + _alert_css()
        + _mismatch_css(mode)
        + (_CB_EXTRA if cb else "")
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_navbar() -> None:
    """Top navigation bar with icons. The Admin link only exists for admins."""
    items = _nav_items()
    with st.container(key="topnav"):
        cols = st.columns([3.2] + [1] * (len(items) + 1), vertical_alignment="center", gap="small")
        cols[0].markdown(
            f'<div class="fm-brand">{_LOGO}<div><b>future me</b><br><small>Plan what\'s next</small></div></div>',
            unsafe_allow_html=True,
        )
        for col, (path, label, icon) in zip(cols[1:-1], items):
            with col:
                st.page_link(path, label=label, icon=icon, width="stretch")
        with cols[-1]:
            with st.popover("Appearance", icon=":material/contrast:", width="stretch"):
                st.markdown("**Appearance & accessibility**")
                appearance_controls("nav")


def page_header(title: str, subtitle: str = "") -> None:
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="finance-header"><h1>{title}</h1>{sub}</div>', unsafe_allow_html=True)


def feature_tiles(tiles) -> None:
    """tiles = [(emoji, title, subtitle), ...] - up to 5 gradient blocks."""
    html = "".join(
        f'<div class="fm-tile"><div class="dots">&bull; &bull; &bull;</div><div class="ico">{i}</div>'
        f'<b>{t}</b><span class="sub">{s}</span></div>'
        for i, t, s in tiles
    )
    st.markdown(f'<div class="fm-tiles">{html}</div>', unsafe_allow_html=True)


def banner(title: str, text: str = "") -> None:
    p = f"<p>{text}</p>" if text else ""
    st.markdown(f'<div class="fm-banner"><h2>{title}</h2>{p}</div>', unsafe_allow_html=True)
