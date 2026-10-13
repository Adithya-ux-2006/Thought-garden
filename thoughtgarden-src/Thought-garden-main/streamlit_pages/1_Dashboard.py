"""Dashboard — quick note input + garden stats.

The note maker here is a plain input: type (title optional — it defaults to
the first line of what you typed) and save. Relationship links are generated
automatically on every save, so the garden grows from typing alone.

Notes render through the shared tg_ui note rows (streamlit_ui), the same
presentation the Flask dashboard uses.
"""

from __future__ import annotations

import streamlit as st

import streamlit_notes_ops as ops
import streamlit_ui as ui
from streamlit_analytics_ops import dashboard_data
from streamlit_auth import current_user_id, require_auth
from streamlit_state import init_state, open_note

st.set_page_config(page_title="Dashboard · Thought Garden", page_icon="🏠", layout="wide")
require_auth()
ui.apply_theme()  # shared tg_ui design (must run inside the page script)
init_state()

user_id = current_user_id()
if user_id is None:
    st.error("No session user.")
    st.stop()


def _go_to_note(note_id: int) -> None:
    open_note(note_id)
    try:
        st.switch_page("streamlit_pages/2_Notes.py")
    except Exception:
        st.info("Open Notes in the sidebar to view this note.")


def _rows(views: list[dict], prefix: str, excerpt: int = 96) -> None:
    """Compact note rows, each with its Open button alongside."""
    for vm in views:
        with st.container(key=f"tgnote-{prefix}-{vm['id']}"):
            c1, c2 = st.columns([7, 1], vertical_alignment="center")
            with c1:
                ui.note_row(vm, excerpt=excerpt)
            with c2, st.container(key=f"tgacts-{prefix}-{vm['id']}"):
                if st.button("Open", key=f"dash_{prefix}_{vm['id']}", use_container_width=True):
                    _go_to_note(vm["id"])


data = dashboard_data(user_id)
stats = data["stats"]

ui.hero(
    "Welcome back",
    "Where your thoughts take root.",
    "Stories, observations, research and half-formed ideas all grow here. "
    "Plant something new below - connections to your other notes are made automatically.",
    stats=[("Notes", stats["total_notes"]), ("Connections", stats["connections"]),
           ("Tags", stats["tags"]), ("Pinned", stats["pinned"]), ("Documents", stats["documents"])],
)


# ── quick note input ─────────────────────────────────────────────────

def quick_note_input() -> None:
    with st.container(border=True, key="tgcomposer"):
        ui.section("Plant a thought", "A story idea, an observation, a question worth keeping.")
        _categories, user_tags = ops.list_filter_choices(user_id)
        with st.form("quick_note", clear_on_submit=True):
            content = st.text_area(
                "What are you thinking?",
                height=140,
                placeholder="Type your note here…",
            )
            c1, c2, c3 = st.columns([2, 2, 2])
            with c1:
                title = st.text_input(
                    "Title (optional)",
                    max_chars=200,
                    placeholder="Defaults to your first line",
                )
            with c2:
                category = st.selectbox(
                    "Category",
                    ops.CATEGORY_OPTIONS,
                    format_func=lambda v: ops.CATEGORY_LABELS.get(v, v),
                    accept_new_options=True,
                    help="Decides the note's flower. Type to create your own category.",
                )
            with c3:
                tags = st.multiselect(
                    "Tags",
                    user_tags,
                    accept_new_options=True,
                    placeholder="story idea, reflection…",
                )
            submitted = st.form_submit_button("Plant it", type="primary")

        if not submitted:
            return
        if not content or not content.strip():
            st.error("Type something first — the note needs content.")
            return

        first_line = next((ln.strip() for ln in content.splitlines() if ln.strip()), "")
        note_title = (title or "").strip() or (first_line[:60] or "Untitled note")

        note_id, warn = ops.create_note(
            user_id,
            title=note_title,
            content=content,
            category=category or "",
            tags=", ".join(tags),
        )
        if warn:
            st.warning(warn)
        else:
            st.success("Planted. Connections generated automatically.")
        _go_to_note(note_id)


quick_note_input()

if stats["total_notes"] == 0:
    st.info("Your garden is empty — plant a first thought above.")
    st.stop()

# ── panels ───────────────────────────────────────────────────────────

left, right = st.columns([3, 2], gap="large")

with left:
    ui.section("Recently planted")
    if data["recent_notes"]:
        _rows(ops.note_views(data["recent_notes"]), "recent")
    else:
        st.caption("Nothing yet.")

with right:
    ui.section("Your flowerbeds")
    if data["categories"]:
        ui.flowerbeds(data["categories"])
    else:
        st.caption("No categories yet.")

    ui.section("Most connected")
    if data["most_connected"]:
        _rows(ops.note_views(note for note, _count in data["most_connected"]), "conn", excerpt=0)
    else:
        st.caption("No connections yet.")

ui.section("Seeds waiting for company",
           "These thoughts haven't found a neighbour yet. A few more words or a shared tag helps them connect.")
if data["orphan_notes"]:
    _rows(ops.note_views(data["orphan_notes"]), "orphan")
else:
    st.caption("Every note is connected. 🌿")

ui.section("Rediscover", "Older thoughts worth another look.")
if data["rediscover"]:
    _rows(ops.note_views(data["rediscover"]), "old")
else:
    st.caption("Nothing old enough to rediscover yet.")
