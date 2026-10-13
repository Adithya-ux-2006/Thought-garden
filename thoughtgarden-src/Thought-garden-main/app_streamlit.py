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
from streamlit_ui import apply_theme

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

# Material Symbols ship with Streamlit (no CDN); line icons like the
# Flask navbar's Bootstrap Icons rather than emoji.
_ICONS = {
    "Dashboard": ":material/home:",
    "Notes": ":material/menu_book:",
    "Garden": ":material/local_florist:",
    "Search": ":material/search:",
    "Insights": ":material/lightbulb:",
    "Profile": ":material/person:",
}


def _build_navigation():
    pages = [
        st.Page(_PAGES[name], title=name, icon=_ICONS[name], default=(name == "Dashboard"))
        for name in _PAGES
    ]
    # A bar across the top, like the Flask app's navbar (and no second copy
    # of the page list in the sidebar, which st.navigation + page_link gave).
    return st.navigation(pages, position="top")


def _sidebar_nav() -> None:
    """Shared sidebar shell: brand, session, garden counts, log out."""
    st.sidebar.title("🌱 Thought Garden")
    st.sidebar.caption("Where your thoughts take root.")
    st.sidebar.divider()
    uid = current_user_id()
    if uid is not None:
        st.sidebar.caption(f"Session user id: {uid}")
    if st.sidebar.button("Log out", use_container_width=True):
        logout()
        st.rerun()


def main() -> None:
    init_state()
    # The shared tg_ui design for the password gate. Each page applies it
    # again inside its own script: the page run replaces anything placed in
    # the (style-only) event container before nav.run().
    apply_theme()
    if not require_auth():
        return

    # Process-level startup (first-run user + relationship backfill) once
    # we're past the gate so a brand-new database still unlocks.
    nav = _build_navigation()

    _sidebar_nav()
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


    nav.run()


main()
