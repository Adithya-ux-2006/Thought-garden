"""Notes page — unified list / view / edit / create via session_state.

Modes: notes_mode ∈ list | view | edit | create
active_note_id selects the note for view/edit.
"""

from __future__ import annotations

import streamlit as st

from streamlit_auth import require_auth, current_user_id
from streamlit_state import (
    KEY_ACTIVE_NOTE_ID,
    KEY_CONFIRM_ACTION,
    KEY_CONFIRM_NOTE_ID,
    KEY_NOTES_ARCHIVED,
    KEY_NOTES_CATEGORY,
    KEY_NOTES_MODE,
    KEY_NOTES_PAGE,
    KEY_NOTES_PINNED_ONLY,
    KEY_NOTES_TAG,
    init_state,
    open_note,
    reset_notes_nav,
)
from streamlit_widgets import (
    PER_PAGE,
    back_to_list,
    clear_confirm_state,
    note_card,
    render_delete_archive_confirm,
    render_pagination,
)
import streamlit_notes_ops as ops

st.set_page_config(page_title="Notes · Thought Garden", page_icon="📝", layout="wide")
require_auth()
init_state()

user_id = current_user_id()
if user_id is None:
    st.error("No session user.")
    st.stop()

mode = st.session_state.get(KEY_NOTES_MODE, "list")
active_id = st.session_state.get(KEY_ACTIVE_NOTE_ID)


# ── helpers ──────────────────────────────────────────────────────────

def _pin_now(note_id: int) -> None:
    ops.toggle_pin(user_id, note_id)
    st.toast("Pin updated")
    st.rerun()


def _request_confirm(action: str, note_id: int) -> None:
    st.session_state[KEY_CONFIRM_ACTION] = action
    st.session_state[KEY_CONFIRM_NOTE_ID] = note_id


def _cancel_confirm() -> None:
    clear_confirm_state()
    st.rerun()


def _do_delete(note_id: int) -> None:
    ops.delete_note(user_id, note_id)
    clear_confirm_state()
    reset_notes_nav("list")
    st.success("Note deleted.")
    st.rerun()


def _do_archive(note_id: int) -> None:
    result = ops.toggle_archive(user_id, note_id)
    clear_confirm_state()
    st.success(f"Note {result}.")
    st.rerun()


# ── LIST ─────────────────────────────────────────────────────────────

def render_list() -> None:
    st.title("Your notes")

    c_back = st.container()
    with c_back:
        col_a, col_b = st.columns([4, 1])
        with col_b:
            if st.button("+ New note", type="primary", use_container_width=True):
                reset_notes_nav("create")
                st.rerun()

    # Filters
    categories, tags = ops.list_filter_choices(user_id)
    with st.container(border=True):
        f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 2, 1])
        with f1:
            st.toggle(
                "Archived",
                key=KEY_NOTES_ARCHIVED,
                on_change=_filter_changed,
            )
        with f2:
            st.toggle(
                "Pinned only",
                key=KEY_NOTES_PINNED_ONLY,
                on_change=_filter_changed,
            )
        with f3:
            st.selectbox(
                "Category",
                [""] + categories,
                format_func=lambda x: x or "All Categories",
                key=KEY_NOTES_CATEGORY,
                on_change=_filter_changed,
            )
        with f4:
            st.selectbox(
                "Tag",
                [""] + tags,
                format_func=lambda x: x or "All Tags",
                key=KEY_NOTES_TAG,
                on_change=_filter_changed,
            )
        with f5:
            st.write("")
            st.write("")
            if st.button("Clear", use_container_width=True):
                st.session_state[KEY_NOTES_ARCHIVED] = False
                st.session_state[KEY_NOTES_PINNED_ONLY] = False
                st.session_state[KEY_NOTES_CATEGORY] = ""
                st.session_state[KEY_NOTES_TAG] = ""
                st.session_state[KEY_NOTES_PAGE] = 1
                st.rerun()

    archived = bool(st.session_state.get(KEY_NOTES_ARCHIVED))
    pinned_only = bool(st.session_state.get(KEY_NOTES_PINNED_ONLY))
    category = st.session_state.get(KEY_NOTES_CATEGORY) or ""
    tag = st.session_state.get(KEY_NOTES_TAG) or ""
    page = int(st.session_state.get(KEY_NOTES_PAGE, 1))

    items, total = ops.query_notes(
        user_id,
        archived=archived,
        pinned_only=pinned_only,
        category=category,
        tag=tag,
        page=page,
        per_page=PER_PAGE,
    )

    # Clamp page if filters shrank results
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    if page > total_pages:
        st.session_state[KEY_NOTES_PAGE] = total_pages
        st.rerun()

    if not items:
        st.info("No notes match these filters.")
        if archived:
            st.caption("You're viewing archived notes.")
        return

    # Card grid — 3 columns
    cols = st.columns(3)
    for i, note in enumerate(items):
        with cols[i % 3]:
            note_card(note, on_open=open_note, on_pin=_pin_now)

    st.divider()
    render_pagination(total, PER_PAGE)


def _filter_changed() -> None:
    st.session_state[KEY_NOTES_PAGE] = 1


# ── VIEW ─────────────────────────────────────────────────────────────

def render_view(note_id: int) -> None:
    try:
        note, related = ops.get_note(user_id, note_id)
    except Exception:
        st.error("Note not found.")
        back_to_list()
        st.rerun()
        return

    if st.button("← Back to notes"):
        back_to_list()
        st.rerun()
        return

    st.title(("📌 " if note.is_pinned else "") + note.title)

    meta_bits = []
    if note.category:
        meta_bits.append(ops.CATEGORY_LABELS.get(note.category, note.category))
    if note.source_type:
        meta_bits.append(note.source_type)
    if note.updated_at:
        meta_bits.append(note.updated_at.strftime("%b %d, %Y"))
    if note.is_archived:
        meta_bits.append("archived")
    st.caption(" · ".join(meta_bits))

    if note.tags:
        st.caption("Tags: " + ", ".join(t.name for t in note.tags))

    # Action row
    a1, a2, a3, a4, a5 = st.columns(5)
    with a1:
        if st.button("Edit", use_container_width=True):
            reset_notes_nav("edit", note.id)
            st.rerun()
    with a2:
        if st.button(("Unpin" if note.is_pinned else "Pin"), use_container_width=True):
            _pin_now(note.id)
    with a3:
        label = "Unarchive" if note.is_archived else "Archive"
        if st.button(label, use_container_width=True):
            _request_confirm("archive", note.id)
    with a4:
        if st.button("Delete", use_container_width=True, type="secondary"):
            _request_confirm("delete", note.id)
    with a5:
        if st.button("Focus in Graph", use_container_width=True):
            from streamlit_state import KEY_GARDEN_FOCUS_ID, KEY_GARDEN_MODE

            st.session_state[KEY_GARDEN_MODE] = "focus"
            st.session_state[KEY_GARDEN_FOCUS_ID] = note.id
            try:
                st.switch_page("streamlit_pages/3_Garden.py")
            except Exception:
                st.info("Open Garden in the sidebar to focus this note.")

    # Confirm panel
    action = st.session_state.get(KEY_CONFIRM_ACTION)
    confirm_nid = st.session_state.get(KEY_CONFIRM_NOTE_ID)
    if action and confirm_nid == note.id:
        if action == "delete":
            render_delete_archive_confirm(
                title=f"Delete “{note.title}”? This cannot be undone.",
                note_id=note.id,
                action="delete",
                on_confirm=_do_delete,
                on_cancel=_cancel_confirm,
            )
        elif action == "archive":
            render_delete_archive_confirm(
                title=f"Archive “{note.title}”? Relationships for this note will be removed.",
                note_id=note.id,
                action="archive",
                on_confirm=_do_archive,
                on_cancel=_cancel_confirm,
            )

    st.divider()
    st.markdown(note.content if note.content.strip() else "*Empty content*")

    if related:
        st.subheader("Related notes")
        for other, sim, rel_type in related:
            with st.container(border=True):
                r1, r2 = st.columns([4, 1])
                with r1:
                    st.markdown(f"**{other.title}**")
                    st.caption(f"{rel_type} · {sim:.0%} · {other.category or 'Uncategorized'}")
                with r2:
                    if st.button("Open", key=f"rel_{other.id}", use_container_width=True):
                        open_note(other.id)
                        st.rerun()


# ── EDIT / CREATE ────────────────────────────────────────────────────

def _note_form(*, note=None, is_create: bool) -> None:
    title_default = ""
    content_default = ""
    category_default = ""
    tags_default = ""
    pinned_default = False

    if note is not None:
        title_default = note.title
        content_default = note.content
        category_default = note.category or ""
        tags_default = ", ".join(t.name for t in note.tags)
        pinned_default = bool(note.is_pinned)

    with st.form("note_form", clear_on_submit=False):
        title = st.text_input("Title", value=title_default, max_chars=200)
        category = st.selectbox(
            "Category",
            ops.CATEGORY_OPTIONS,
            index=ops.CATEGORY_OPTIONS.index(category_default)
            if category_default in ops.CATEGORY_OPTIONS
            else 0,
            format_func=lambda v: ops.CATEGORY_LABELS.get(v, v),
        )
        tags = st.text_input("Tags (comma-separated)", value=tags_default)
        content = st.text_area("Content", value=content_default, height=280)
        is_pinned = st.checkbox("Pin this note", value=pinned_default)
        submitted = st.form_submit_button("Save Note", type="primary")

    if submitted:
        errors = []
        if not title or not title.strip():
            errors.append("Title is required.")
        elif len(title) > 200:
            errors.append("Title must be 200 characters or fewer.")
        if not content or not content.strip():
            errors.append("Content is required.")
        if errors:
            for e in errors:
                st.error(e)
            return

        if is_create:
            note_id, warn = ops.create_note(
                user_id,
                title=title.strip(),
                content=content,
                category=category,
                tags=tags,
                is_pinned=is_pinned,
            )
            if warn:
                st.warning(warn)
            else:
                st.success("Note created successfully!")
            reset_notes_nav("view", note_id)
            st.rerun()
        else:
            warn = ops.update_note(
                user_id,
                note.id,
                title=title.strip(),
                content=content,
                category=category,
                tags=tags,
                is_pinned=is_pinned,
            )
            if warn:
                st.warning(warn)
            else:
                st.success("Note updated successfully!")
            reset_notes_nav("view", note.id)
            st.rerun()


def render_import() -> None:
    with st.expander("Import document (PDF / TXT / MD)"):
        uploaded = st.file_uploader(
            "Document", type=["pdf", "txt", "md"], key="note_import_file"
        )
        imp_cat = st.selectbox(
            "Category for import",
            ops.CATEGORY_OPTIONS,
            index=0,
            format_func=lambda v: ops.CATEGORY_LABELS.get(v, v),
            key="note_import_category",
        )
        if st.button("Import Document", disabled=uploaded is None):
            ids, err = ops.import_document(user_id, uploaded, imp_cat)
            if err:
                st.error(err)
            else:
                st.success(f"Successfully imported {len(ids)} note(s) from {uploaded.name}")
                if len(ids) == 1:
                    reset_notes_nav("view", ids[0])
                else:
                    reset_notes_nav("list")
                st.rerun()


def render_create() -> None:
    st.title("New note")
    if st.button("← Cancel"):
        back_to_list()
        st.rerun()
        return
    _note_form(note=None, is_create=True)
    st.divider()
    render_import()


def render_edit(note_id: int) -> None:
    try:
        note, _ = ops.get_note(user_id, note_id)
    except Exception:
        st.error("Note not found.")
        back_to_list()
        st.rerun()
        return

    st.title(f"Edit: {note.title}")
    if st.button("← Cancel"):
        reset_notes_nav("view", note.id)
        st.rerun()
        return
    _note_form(note=note, is_create=False)


# ── dispatch ─────────────────────────────────────────────────────────

if mode == "view" and active_id:
    render_view(active_id)
elif mode == "edit" and active_id:
    render_edit(active_id)
elif mode == "create":
    render_create()
else:
    render_list()
