"""Knowledge Garden — vis-network graph, full view or focus view.

Port of Flask app/garden/routes.py: same payloads, same category filter
(the checkboxes actually filter here — REM-001 from the Flask app),
growth-stage icons, click-to-highlight-neighbourhood.
"""

from __future__ import annotations

import streamlit as st

import streamlit_garden_ops as garden
from streamlit_auth import current_user_id, require_auth
from streamlit_state import (
    KEY_GARDEN_CATEGORIES,
    KEY_GARDEN_FOCUS_ID,
    KEY_GARDEN_MODE,
    KEY_GARDEN_SEARCH,
    init_state,
    open_note,
)

st.set_page_config(page_title="Garden · Thought Garden", page_icon="🌱", layout="wide")
require_auth()
init_state()

user_id = current_user_id()
if user_id is None:
    st.error("No session user.")
    st.stop()

if "garden_physics" not in st.session_state:
    st.session_state["garden_physics"] = True


def _open(note_id: int) -> None:
    open_note(note_id)
    try:
        st.switch_page("streamlit_pages/2_Notes.py")
    except Exception:
        st.info("Open Notes in the sidebar to view this note.")


st.title("Knowledge Garden")
st.caption(
    "Nodes are notes — the plant grows as a note ages and gains connections. "
    "Click a node to highlight its neighbourhood."
)

choices = garden.note_choices(user_id)
if not choices:
    st.info("Your garden is empty — add a note from the Dashboard and it appears here.")
    st.stop()

by_id = dict(choices)
categories = garden.list_categories(user_id)

# ── toolbar ──────────────────────────────────────────────────────────

with st.container(border=True):
    r1, r2, r3 = st.columns([2, 3, 3])
    with r1:
        mode = st.radio(
            "View",
            ["full", "focus"],
            format_func=lambda m: {"full": "Whole garden", "focus": "Focus"}[m],
            index=0 if st.session_state[KEY_GARDEN_MODE] == "full" else 1,
            horizontal=True,
            key="garden_mode_radio",
        )
        st.session_state[KEY_GARDEN_MODE] = mode
    with r2:
        if mode == "focus":
            focus_id = st.selectbox(
                "Focus note",
                [c[0] for c in choices],
                format_func=lambda i: by_id.get(i, "?"),
                index=max(
                    0,
                    [c[0] for c in choices].index(st.session_state[KEY_GARDEN_FOCUS_ID])
                    if st.session_state[KEY_GARDEN_FOCUS_ID] in by_id
                    else 0,
                ),
                key="garden_focus_select",
            )
            st.session_state[KEY_GARDEN_FOCUS_ID] = focus_id
        else:
            picked = st.multiselect(
                "Categories",
                categories,
                default=[
                    c for c in st.session_state[KEY_GARDEN_CATEGORIES] if c in categories
                ],
                key="garden_category_multiselect",
            )
            st.session_state[KEY_GARDEN_CATEGORIES] = picked
    with r3:
        s1, s2 = st.columns([3, 1])
        with s1:
            search = st.text_input(
                "Find in graph",
                placeholder="Highlight a note by title…",
                key="garden_search_input",
            )
            st.session_state[KEY_GARDEN_SEARCH] = search
        with s2:
            st.write("")
            physics = st.toggle("Physics", value=st.session_state["garden_physics"],
                                key="garden_physics_toggle")
            st.session_state["garden_physics"] = physics

selected_categories = st.session_state[KEY_GARDEN_CATEGORIES] or None

if mode == "focus" and st.session_state[KEY_GARDEN_FOCUS_ID] is None:
    st.session_state[KEY_GARDEN_FOCUS_ID] = choices[0][0]

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
        payload = garden.garden_payload(user_id, selected_categories)

garden.render_graph(
    payload,
    height=540,
    physics=st.session_state["garden_physics"],
    search=st.session_state[KEY_GARDEN_SEARCH],
)

st.caption(
    f"{len(payload['nodes'])} note{'s' if len(payload['nodes']) != 1 else ''} · "
    f"{len(payload['edges'])} connection{'s' if len(payload['edges']) != 1 else ''}"
)

# ── side list ────────────────────────────────────────────────────────

st.subheader("Notes in the garden")

columns = st.columns(3)
for i, (note_id, title) in enumerate(choices):
    with columns[i % 3].container(border=True):
        st.markdown(f"**{title}**")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Open", key=f"gar_open_{note_id}", use_container_width=True):
                _open(note_id)
        with b2:
            if st.button("Focus", key=f"gar_focus_{note_id}", use_container_width=True):
                st.session_state[KEY_GARDEN_FOCUS_ID] = note_id
                st.session_state[KEY_GARDEN_MODE] = "focus"
                # The widgets below have their own keys — write those too or
                # they'd snap back to their old values on the rerun.
                st.session_state["garden_focus_select"] = note_id
                st.session_state["garden_mode_radio"] = "focus"
                st.rerun()
