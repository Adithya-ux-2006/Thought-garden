"""Session-state keys and defaults for the Streamlit port."""

from __future__ import annotations

import streamlit as st

# Keys written by the auth gate / entry
KEY_AUTH_OK = "auth_ok"
KEY_USER_ID = "user_id"
KEY_GATE_ERROR = "gate_error"

# Notes page sub-view
KEY_NOTES_MODE = "notes_mode"  # list | view | edit | create
KEY_ACTIVE_NOTE_ID = "active_note_id"
KEY_NOTES_PAGE = "notes_page"
KEY_NOTES_ARCHIVED = "notes_archived"
KEY_NOTES_PINNED_ONLY = "notes_pinned_only"
KEY_NOTES_CATEGORY = "notes_category"
KEY_NOTES_TAG = "notes_tag"

# Confirm dialogs (delete / archive)
KEY_CONFIRM_ACTION = "confirm_action"  # None | "delete" | "archive"
KEY_CONFIRM_NOTE_ID = "confirm_note_id"

# Garden
KEY_GARDEN_MODE = "garden_mode"  # full | focus
KEY_GARDEN_FOCUS_ID = "garden_focus_id"
KEY_GARDEN_SEARCH = "garden_search"
KEY_GARDEN_CATEGORIES = "garden_categories"  # list of enabled category names

# Search
KEY_SEARCH_QUERY = "search_query"
KEY_SEARCH_CATEGORY = "search_category"
KEY_SEARCH_TAG = "search_tag"
KEY_SEARCH_SOURCE = "search_source"
KEY_SEARCH_PAGE = "search_page"
KEY_SEARCH_RAN = "search_ran"

DEFAULTS = {
    KEY_AUTH_OK: False,
    KEY_USER_ID: None,
    KEY_GATE_ERROR: None,
    KEY_NOTES_MODE: "list",
    KEY_ACTIVE_NOTE_ID: None,
    KEY_NOTES_PAGE: 1,
    KEY_NOTES_ARCHIVED: False,
    KEY_NOTES_PINNED_ONLY: False,
    KEY_NOTES_CATEGORY: "",
    KEY_NOTES_TAG: "",
    KEY_CONFIRM_ACTION: None,
    KEY_CONFIRM_NOTE_ID: None,
    KEY_GARDEN_MODE: "full",
    KEY_GARDEN_FOCUS_ID: None,
    KEY_GARDEN_SEARCH: "",
    KEY_GARDEN_CATEGORIES: [],
    KEY_SEARCH_QUERY: "",
    KEY_SEARCH_CATEGORY: "",
    KEY_SEARCH_TAG: "",
    KEY_SEARCH_SOURCE: "",
    KEY_SEARCH_PAGE: 1,
    KEY_SEARCH_RAN: False,
}


def init_state() -> None:
    """Ensure every known key exists (safe to call every rerun)."""
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def reset_notes_nav(mode: str = "list", note_id: int | None = None) -> None:
    st.session_state[KEY_NOTES_MODE] = mode
    st.session_state[KEY_ACTIVE_NOTE_ID] = note_id
    st.session_state[KEY_CONFIRM_ACTION] = None
    st.session_state[KEY_CONFIRM_NOTE_ID] = None


def open_note(note_id: int) -> None:
    """Jump to Notes view for a note (used by Garden side-list, etc.)."""
    reset_notes_nav("view", note_id)
    st.session_state[KEY_NOTES_PAGE] = 1
