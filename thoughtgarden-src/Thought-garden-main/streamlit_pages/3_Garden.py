"""Knowledge Garden — the shared tg_ui garden (same JS/CSS/flowers as the
Flask garden page), whole garden or focused on one note.

Category chips, search, zoom/fit/physics and the journal side panel all
live inside the garden component (streamlit_ui.garden); its Open / Edit /
Focus actions come back here as component values. The list below the
graph is the text alternative to the canvas.
"""

from __future__ import annotations

import streamlit as st

import streamlit_garden_ops as garden
import streamlit_ui as ui
from streamlit_auth import current_user_id, require_auth
from streamlit_state import (
    KEY_GARDEN_FOCUS_ID,
    KEY_GARDEN_MODE,
    KEY_NOTES_MODE,
    init_state,
    open_note,
    reset_notes_nav,
)

st.set_page_config(page_title="Garden · Thought Garden", page_icon="🌱", layout="wide")
require_auth()
ui.apply_theme()  # shared tg_ui design (must run inside the page script)
init_state()

user_id = current_user_id()
if user_id is None:
    st.error("No session user.")
    st.stop()

KEY_LAST_ACTION = "garden_last_action"


def _go_notes() -> None:
    try:
        st.switch_page("streamlit_pages/2_Notes.py")
    except Exception:
        st.info("Open Notes in the sidebar to continue.")


def _focus(note_id: int) -> None:
    st.session_state[KEY_GARDEN_FOCUS_ID] = note_id
    st.session_state[KEY_GARDEN_MODE] = "focus"
    # The widgets below have their own keys — write those too or they'd
    # snap back to their old values on the rerun.
    st.session_state["garden_focus_select"] = note_id
    st.session_state["garden_mode_radio"] = "focus"
    st.rerun()


def _handle(action: dict | None) -> None:
    """Act once on an Open / Edit / Focus / Plant click from the garden."""
    if not action or action.get("nonce") == st.session_state.get(KEY_LAST_ACTION):
        return
    st.session_state[KEY_LAST_ACTION] = action.get("nonce")
    kind, note_id = action.get("action"), action.get("id")
    if kind == "open" and note_id:
        open_note(note_id)
        _go_notes()
    elif kind == "edit" and note_id:
        reset_notes_nav("edit", note_id)
        _go_notes()
    elif kind == "focus" and note_id:
        _focus(note_id)
    elif kind == "create":
        st.session_state[KEY_NOTES_MODE] = "create"
        _go_notes()


choices = garden.note_choices(user_id)

ui.hero(
    "My garden",
    "Knowledge Garden",
    "Every note is a plant: it grows with age and connections, then blooms into its "
    "category's flower. Click one to open its page.",
)

if not choices:
    st.info("Your garden is empty — plant a thought from the Dashboard and it appears here.")
    st.stop()

by_id = dict(choices)

# Widget keys start from the page's own state (another page - Notes'
# "Focus in Graph" - may have set it); Streamlit drops widget keys when you
# leave a page, so this runs again on every visit.
ids = [c[0] for c in choices]
if st.session_state[KEY_GARDEN_FOCUS_ID] not in by_id:
    st.session_state[KEY_GARDEN_FOCUS_ID] = ids[0]
st.session_state.setdefault("garden_mode_radio", st.session_state[KEY_GARDEN_MODE])
if st.session_state.get("garden_focus_select") not in by_id:
    st.session_state["garden_focus_select"] = st.session_state[KEY_GARDEN_FOCUS_ID]

with st.container(key="tggarden-controls"):
    r1, r2 = st.columns([2, 5])
    with r1:
        mode = st.segmented_control(
            "View",
            ["full", "focus"],
            format_func=lambda m: {"full": "Whole garden", "focus": "Focus on a note"}[m],
            key="garden_mode_radio",
        ) or "full"
        st.session_state[KEY_GARDEN_MODE] = mode
    with r2:
        if mode == "focus":
            focus_id = st.selectbox(
                "Focus note",
                ids,
                format_func=lambda i: by_id.get(i, "?"),
                key="garden_focus_select",
            )
            st.session_state[KEY_GARDEN_FOCUS_ID] = focus_id

with st.spinner("Growing your garden…"):
    if mode == "focus":
        payload = garden.focus_payload(user_id, st.session_state[KEY_GARDEN_FOCUS_ID])
        if not payload["nodes"]:
            st.warning(
                "That note has no connections in range yet — switch to the "
                "whole garden, or write a few more notes."
            )
            st.stop()
    else:
        payload = garden.garden_payload(user_id)

_handle(ui.garden(payload, height=760))

# ── the garden as text ───────────────────────────────────────────────

with st.expander(f"All {len(choices)} plants as a list", expanded=False):
    for note_id, title in choices:
        c1, c2, c3 = st.columns([6, 1, 1])
        with c1:
            st.markdown(f"**{title}**")
        with c2:
            if st.button("Open", key=f"gar_open_{note_id}", use_container_width=True):
                open_note(note_id)
                _go_notes()
        with c3:
            if st.button("Focus", key=f"gar_focus_{note_id}", use_container_width=True):
                _focus(note_id)
