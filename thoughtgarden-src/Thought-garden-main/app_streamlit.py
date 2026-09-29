"""Thought Garden — Streamlit entrypoint.

Replaces run.py's Flask server. Run with:

    streamlit run app_streamlit.py

Startup (first-run local user + ensure_all_relationships) runs once per
process inside streamlit_db.run_startup_once(). No demo notes are seeded.
"""

from __future__ import annotations

import streamlit as st

from streamlit_auth import current_user_id, logout, require_auth
from streamlit_state import init_state

st.set_page_config(
    page_title="Thought Garden",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

_PAGES = {
    "Dashboard": "streamlit_pages/1_Dashboard.py",
    "Notes": "streamlit_pages/2_Notes.py",
    "Garden": "streamlit_pages/3_Garden.py",
    "Search": "streamlit_pages/4_Search.py",
    "Insights": "streamlit_pages/5_Insights.py",
    "Profile": "streamlit_pages/6_Profile.py",
}

_ICONS = {
    "Dashboard": "🏠",
    "Notes": "📝",
    "Garden": "🌿",
    "Search": "🔍",
    "Insights": "📈",
    "Profile": "👤",
}


def _build_navigation():
    pages = [
        st.Page(_PAGES[name], title=name, icon=_ICONS[name], default=(name == "Dashboard"))
        for name in _PAGES
    ]
    return st.navigation(pages)


def _sidebar_nav() -> None:
    """Shared sidebar shell (replaces base.html navbar)."""
    st.sidebar.title("🌱 Thought Garden")

    # page_link entries for quick jump (navigation itself owns active state)
    for name, path in _PAGES.items():
        st.sidebar.page_link(path, label=name, icon=_ICONS[name])

    st.sidebar.divider()
    uid = current_user_id()
    if uid is not None:
        st.sidebar.caption(f"Session user id: {uid}")
    if st.sidebar.button("Log out", use_container_width=True):
        logout()
        st.rerun()


def main() -> None:
    init_state()
    if not require_auth():
        return

    # Process-level startup (first-run user + relationship backfill) once
    # we're past the gate so a brand-new database still unlocks.
    try:
        from streamlit_db import run_startup_once

        info = run_startup_once()
        st.sidebar.caption(
            f"Garden: {info.get('note_count', 0)} note"
            f"{'s' if info.get('note_count', 0) != 1 else ''} · "
            f"{info.get('connection_count', 0)} connection"
            f"{'s' if info.get('connection_count', 0) != 1 else ''}"
        )
    except Exception as exc:  # surface startup failures instead of blank page
        st.sidebar.error(f"Startup issue: {exc}")

    _sidebar_nav()

    nav = _build_navigation()
    nav.run()


main()
