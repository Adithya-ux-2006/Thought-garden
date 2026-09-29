"""Dashboard — quick note input + garden stats.

The note maker here is a plain input: type (title optional — it defaults to
the first line of what you typed) and save. Relationship links are generated
automatically on every save, so the garden grows from typing alone.
"""

from __future__ import annotations

import streamlit as st

import streamlit_notes_ops as ops
from streamlit_analytics_ops import dashboard_data
from streamlit_auth import current_user_id, require_auth
from streamlit_state import init_state, open_note

st.set_page_config(page_title="Dashboard · Thought Garden", page_icon="🏠", layout="wide")
require_auth()
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


# ── quick note input ─────────────────────────────────────────────────

st.title("Dashboard")
st.caption("Type a note below — connections to your other notes are made automatically.")


def quick_note_input() -> None:
    with st.container(border=True):
        st.subheader("New note")
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
                )
            with c3:
                tags = st.text_input("Tags (comma-separated)", placeholder="e.g. notes, topic")
            submitted = st.form_submit_button("Add to garden", type="primary")

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
            category=category,
            tags=tags,
        )
        if warn:
            st.warning(warn)
        else:
            st.success("Saved. Connections generated automatically.")
        _go_to_note(note_id)


quick_note_input()

# ── stats + panels ───────────────────────────────────────────────────

data = dashboard_data(user_id)
stats = data["stats"]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Notes", stats["total_notes"])
m2.metric("Connections", stats["connections"])
m3.metric("Tags", stats["tags"])
m4.metric("Pinned", stats["pinned"])
m5.metric("Documents", stats["documents"])

st.divider()

if stats["total_notes"] == 0:
    st.info("Your garden is empty — type a note above to plant the first one.")
    st.stop()

left, right = st.columns(2)

with left:
    st.subheader("Recently added")
    if data["recent_notes"]:
        for note in data["recent_notes"]:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{'📌 ' if note.is_pinned else ''}{note.title}**")
                    st.caption(
                        (note.category or "Uncategorized")
                        + " · "
                        + (note.created_at.strftime("%b %d, %Y") if note.created_at else "")
                    )
                with c2:
                    if st.button("Open", key=f"dash_open_{note.id}", use_container_width=True):
                        _go_to_note(note.id)
    else:
        st.caption("Nothing yet.")

    st.subheader("Orphan notes")
    if data["orphan_notes"]:
        st.caption("No connections yet — they'll link as your garden grows.")
        for note in data["orphan_notes"]:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{note.title}**")
                with c2:
                    if st.button(
                        "Open", key=f"dash_orphan_{note.id}", use_container_width=True
                    ):
                        _go_to_note(note.id)
    else:
        st.caption("Every note is connected. 🌿")

with right:
    st.subheader("Most connected")
    if data["most_connected"]:
        for note, count in data["most_connected"]:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{note.title}**")
                    st.caption(f"{count} connection{'s' if count != 1 else ''}")
                with c2:
                    if st.button(
                        "Open", key=f"dash_conn_{note.id}", use_container_width=True
                    ):
                        _go_to_note(note.id)
    else:
        st.caption("No connections yet.")

    st.subheader("Categories")
    if data["categories"]:
        for category, count in data["categories"]:
            st.progress(
                min(count / max(stats["total_notes"], 1), 1.0),
                text=f"{category} · {count}",
            )
    else:
        st.caption("No categories yet.")

    st.subheader("Rediscover")
    if data["rediscover"]:
        for note in data["rediscover"]:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{note.title}**")
                    st.caption(note.content[:100] + ("..." if len(note.content) > 100 else ""))
                with c2:
                    if st.button(
                        "Open", key=f"dash_old_{note.id}", use_container_width=True
                    ):
                        _go_to_note(note.id)
    else:
        st.caption("Nothing old enough to rediscover yet.")
