"""
Shared sign-in gate + Felbry College branding for every page of the
Streamlit app (app.py and all of pages/*.py).

Why this exists: the dashboard page's own HTML (dashboard_template.html)
already had a branded email/password overlay, but that overlay lives
*inside* the Dashboard page's embedded HTML -- it never protected the
Upload Data or Run Analysis pages at all, and it only ever looked like
Felbry College once you were already on the Dashboard page. This module
fixes both: `require_login()` gates every page (including the two that
were previously wide open) from a single shared session-state flag, and
`inject_branding()` applies the same maroon/teal Felbry look to the
Streamlit chrome itself (buttons, inputs, the top banner), not just the
HTML dashboard.

This is a convenience layer, NOT the real access control -- same caveat
as the dashboard's original password gate: the password is visible to
anyone who reads this file, so it mainly deters casual link-sharing. The
actual access control for the deployed app is Streamlit Community Cloud's
own "Only specific people" viewer allowlist (Settings -> Sharing), which
shows a real Google sign-in before this app even loads -- see README.md.
This gate is an additional, explicit layer the user asked for on top of
that, consistent with the same hardcoded password ("admin") already used
for the standalone dashboard Artifact link, which has no backend at all.
"""
from __future__ import annotations

import base64
import os

import streamlit as st

LOGIN_PASSWORD = "admin"

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGO_PATH = os.path.join(_REPO_ROOT, "felbry_logo.png")

BRAND_MAROON = "#83010c"
BRAND_MAROON_DARK = "#5e0109"
BRAND_TEAL = "#5d9ab6"
BRAND_NEUTRAL = "#f4f4f4"


@st.cache_data(show_spinner=False)
def _logo_b64() -> str | None:
    try:
        with open(_LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return None


def _global_css() -> str:
    """CSS applied on every page, logged in or not: Felbry colors on top of
    Streamlit's own widgets (buttons, inputs, tabs, metrics, the sidebar),
    plus hiding the auto-generated page list in the sidebar until the
    viewer is signed in (so the app's structure isn't visible pre-login)."""
    hide_nav = (
        '[data-testid="stSidebarNav"] { display: none; }'
        if not st.session_state.get("felbry_authed") else ""
    )
    return f"""
    <style>
      :root {{
        --felbry-maroon: {BRAND_MAROON};
        --felbry-maroon-dark: {BRAND_MAROON_DARK};
        --felbry-teal: {BRAND_TEAL};
      }}
      {hide_nav}
      /* Buttons */
      .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
        background-color: var(--felbry-maroon);
        color: #fff;
        border: 1px solid var(--felbry-maroon);
        border-radius: 8px;
      }}
      .stButton > button:hover, .stDownloadButton > button:hover,
      .stFormSubmitButton > button:hover {{
        background-color: var(--felbry-maroon-dark);
        border-color: var(--felbry-maroon-dark);
        color: #fff;
      }}
      .stButton > button:disabled {{
        background-color: #c9c9c9; border-color: #c9c9c9; color: #777;
      }}
      /* Inputs, selects, file uploader focus rings */
      input:focus, textarea:focus, [data-baseweb="select"]:focus-within,
      [data-testid="stFileUploaderDropzone"]:focus-within {{
        outline: none !important;
        box-shadow: 0 0 0 2px var(--felbry-teal) !important;
        border-color: var(--felbry-teal) !important;
      }}
      /* Progress / spinner accents */
      .stProgress > div > div > div > div {{ background-color: var(--felbry-teal); }}
      [data-testid="stSpinner"] svg {{ color: var(--felbry-maroon); }}
      /* Sidebar */
      [data-testid="stSidebar"] {{
        background-color: #fbfafa;
        border-right: 1px solid #e8e3e3;
      }}
      /* Links */
      a {{ color: var(--felbry-maroon); }}
      /* Metric labels/values pick up a touch of brand color */
      [data-testid="stMetricValue"] {{ color: var(--felbry-maroon-dark); }}
    </style>
    """


def inject_branding(page_label: str = "") -> None:
    """Call once near the top of every page (after st.set_page_config and
    require_login()). Draws a slim maroon banner with the real Felbry
    College logo and applies the shared brand CSS. `page_label` is an
    optional right-aligned tag (e.g. "Upload Data") shown next to the logo
    so staff always know which of the 3 pages they're on even before the
    page's own heading renders."""
    st.markdown(_global_css(), unsafe_allow_html=True)
    logo_b64 = _logo_b64()
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" style="height:38px;width:auto;display:block;" />'
        if logo_b64 else
        '<span style="color:#fff;font-weight:700;font-size:15px;">Felbry College</span>'
    )
    label_html = (
        f'<span style="color:#f2d9da;font-size:12.5px;font-weight:600;'
        f'letter-spacing:.02em;">{page_label}</span>'
        if page_label else ""
    )
    st.markdown(
        f"""
        <div style="background:var(--felbry-maroon,{BRAND_MAROON});
                    margin:-1rem -1rem 1.2rem -1rem;
                    padding:12px 28px;
                    display:flex; align-items:center; justify-content:space-between;
                    border-bottom:3px solid var(--felbry-teal,{BRAND_TEAL});">
          <div style="display:flex;align-items:center;gap:12px;">
            {logo_html}
            <span style="color:#fff;font-size:13px;font-weight:600;opacity:.92;">
              KPI System
            </span>
          </div>
          {label_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def require_login() -> None:
    """Gate the ENTIRE page behind a single shared sign-in check, backed by
    st.session_state (shared across every page of the app within one
    browser session). Must be the first thing called after
    st.set_page_config() on every page -- app.py and all of pages/*.py --
    so none of them (including Upload Data / Run Analysis, which previously
    had no gate at all) render anything before the viewer signs in once."""
    if st.session_state.get("felbry_authed"):
        return

    st.markdown(_global_css(), unsafe_allow_html=True)
    logo_b64 = _logo_b64()
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;max-width:220px;height:auto;display:block;margin:0 auto;" />'
        if logo_b64 else
        '<div style="color:#fff;font-weight:700;font-size:20px;text-align:center;">Felbry College</div>'
    )
    st.markdown(
        f"""
        <div style="max-width:380px;margin:9vh auto 0;border-radius:12px;overflow:hidden;
                    box-shadow:0 2px 24px rgba(0,0,0,.12);border:1px solid #e8e3e3;">
          <div style="background:{BRAND_MAROON};padding:26px 24px;">
            {logo_html}
          </div>
          <div style="background:#fff;padding:18px 24px 6px;text-align:center;
                      font-size:12.5px;color:#6b6b6b;">
            Operations &amp; Student Success Dashboard
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p style="text-align:center;color:#999;font-size:11px;margin-top:18px;">'
        "Felbry College staff only</p>",
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        with st.form("felbry_login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            if not email.strip():
                st.error("Please enter an email address.")
            elif password != LOGIN_PASSWORD:
                st.error("Incorrect password.")
            else:
                st.session_state["felbry_authed"] = True
                st.session_state["felbry_email"] = email.strip()
                st.rerun()

    st.stop()


def sidebar_signout() -> None:
    """Optional small sign-out control -- call after inject_branding() on
    any page. Clears the shared session flag so the next page render (this
    page, on rerun, or any other page the viewer switches to) shows the
    login gate again."""
    with st.sidebar:
        st.divider()
        email = st.session_state.get("felbry_email")
        if email:
            st.caption(f"Signed in as **{email}**")
        if st.button("Sign out", use_container_width=True):
            st.session_state.pop("felbry_authed", None)
            st.session_state.pop("felbry_email", None)
            st.rerun()
