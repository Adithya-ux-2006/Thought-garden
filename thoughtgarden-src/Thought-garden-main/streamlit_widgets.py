"""Shared Streamlit widgets for notes (cards, confirm, pagination)."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable, Sequence

import streamlit as st

from streamlit_state import (
    KEY_CONFIRM_ACTION,
    KEY_CONFIRM_NOTE_ID,
    KEY_NOTES_PAGE,
    reset_notes_nav,
)

PER_PAGE = 12


def parse_tags(tag_string: str | None) -> list[str]:
    if not tag_string:
        return []
    return [t.strip() for t in tag_string.split(",") if t.strip()]


def note_card(note, *, on_open: Callable[[int], None], on_pin: Callable[[int], None] | None = None) -> None:
    """Render one note card. on_open/on_pin receive note.id."""
    pinned = "📌 " if note.is_pinned else ""
    updated = note.updated_at.strftime("%b %d, %Y") if note.updated_at else ""

    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"**{pinned}{note.title}**")
            preview = note.content[:150] + ("..." if len(note.content) > 150 else "")
            st.caption(preview)
            badges = []
            if note.category:
                badges.append(note.category)
            for t in note.tags[:3]:
                badges.append(t.name)
            if len(note.tags) > 3:
                badges.append(f"+{len(note.tags) - 3}")
            if badges:
                st.caption(" · ".join(badges))
            st.caption(updated)
        with c2:
            if st.button("Open", key=f"open_{note.id}", use_container_width=True):
                on_open(note.id)
            if on_pin is not None:
                label = "Unpin" if note.is_pinned else "Pin"
                if st.button(label, key=f"pin_{note.id}", use_container_width=True):
                    on_pin(note.id)


def render_pagination(total: int, per_page: int = PER_PAGE) -> None:
    """Prev/Next buttons driven by session_state.notes_page."""
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = int(st.session_state.get(KEY_NOTES_PAGE, 1))
    page = min(max(1, page), total_pages)
    st.session_state[KEY_NOTES_PAGE] = page

    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        disabled_prev = page <= 1
        if st.button("← Prev", disabled=disabled_prev, use_container_width=True):
            st.session_state[KEY_NOTES_PAGE] = page - 1
            st.rerun()
    with c2:
        st.caption(f"Page {page} of {total_pages} · {total} note{'s' if total != 1 else ''}")
    with c3:
        disabled_next = page >= total_pages
        if st.button("Next →", disabled=disabled_next, use_container_width=True):
            st.session_state[KEY_NOTES_PAGE] = page + 1
            st.rerun()


def render_delete_archive_confirm(
    *,
    title: str,
    note_id: int,
    action: str,
    on_confirm: Callable[[int], None],
    on_cancel: Callable[[], None],
) -> None:
    """Checkbox + button confirm for destructive delete/archive.

    activation sets st.session_state[KEY_CONFIRM_ACTION] before calling this.
    """
    st.warning(title)
    st.checkbox(
        "I understand this action",
        key=f"confirm_ack_{action}_{note_id}",
        value=False,
    )
    ack = st.session_state.get(f"confirm_ack_{action}_{note_id}", False)
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"Confirm {action}", type="primary", disabled=not ack, use_container_width=True):
            on_confirm(note_id)
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state[f"confirm_ack_{action}_{note_id}"] = False
            on_cancel()


def clear_confirm_state() -> None:
    st.session_state[KEY_CONFIRM_ACTION] = None
    st.session_state[KEY_CONFIRM_NOTE_ID] = None


def back_to_list() -> None:
    reset_notes_nav("list")
