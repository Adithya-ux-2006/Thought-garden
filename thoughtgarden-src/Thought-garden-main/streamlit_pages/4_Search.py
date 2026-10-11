"""Search — hybrid (keyword + semantic) search with filters and paging.

Port of Flask app/search/routes.py: same hybrid_search() call, same
filters, same pagination semantics. Falls back to keyword-only search if
the embedding model can't be loaded (first run offline, for example).
"""

from __future__ import annotations

import streamlit as st

import streamlit_notes_ops as ops
from streamlit_auth import current_user_id, require_auth
from streamlit_state import (
    KEY_SEARCH_CATEGORY,
    KEY_SEARCH_PAGE,
    KEY_SEARCH_QUERY,
    KEY_SEARCH_RAN,
    KEY_SEARCH_SOURCE,
    KEY_SEARCH_TAG,
    init_state,
    open_note,
)
from streamlit_widgets import PER_PAGE

st.set_page_config(page_title="Search · Thought Garden", page_icon="🔍", layout="wide")
require_auth()
init_state()

user_id = current_user_id()
if user_id is None:
    st.error("No session user.")
    st.stop()

PER_PAGE_SEARCH = 10


def _run_search(query: str, category: str, tag: str, source: str, mode: str):
    from app.services.search_service import hybrid_search, keyword_search
    from streamlit_analytics_ops import _materialize
    from streamlit_db import app_context

    kwargs = dict(
        category=category or None,
        tag=tag or None,
        source_type=source or None,
    )
    page = st.session_state[KEY_SEARCH_PAGE]

    def _ready(pagination):
        # Touch relations now: once the app context exits these rows detach.
        _materialize(pagination.items)
        return pagination

    with app_context():
        if mode == "Keyword only" or not query:
            return _ready(keyword_search(user_id, query, page=page,
                                         per_page=PER_PAGE_SEARCH, **kwargs)), None
        try:
            return _ready(hybrid_search(user_id, query, page=page,
                                        per_page=PER_PAGE_SEARCH, **kwargs)), None
        except Exception as exc:  # model load/network failure — degrade, don't 500
            return _ready(keyword_search(user_id, query, page=page,
                                         per_page=PER_PAGE_SEARCH, **kwargs)), (
                f"Semantic search unavailable ({exc.__class__.__name__}) — "
                "showing keyword results only."
            )


st.title("Search")

categories, tags = ops.list_filter_choices(user_id)
sources = ["", "manual", "document"]

with st.container(border=True):
    with st.form("search_form"):
        q1, q2 = st.columns([4, 1])
        with q1:
            query = st.text_input(
                "Query",
                value=st.session_state.get(KEY_SEARCH_QUERY, ""),
                placeholder="Search titles and content…",
            )
        with q2:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Search", type="primary")

        f1, f2, f3, f4 = st.columns(4)
        with f1:
            category = st.selectbox(
                "Category",
                [""] + categories,
                format_func=lambda x: x or "All Categories",
                key=KEY_SEARCH_CATEGORY,
            )
        with f2:
            tag = st.selectbox(
                "Tag",
                [""] + tags,
                format_func=lambda x: x or "All Tags",
                key=KEY_SEARCH_TAG,
            )
        with f3:
            source = st.selectbox(
                "Source",
                sources,
                format_func=lambda x: {"": "All Sources", "manual": "Typed",
                                       "document": "Imported"}.get(x, x),
                key=KEY_SEARCH_SOURCE,
            )
        with f4:
            mode = st.selectbox("Mode", ["Hybrid", "Keyword only"], key="search_mode_input")

if submitted:
    st.session_state[KEY_SEARCH_QUERY] = query
    st.session_state[KEY_SEARCH_PAGE] = 1
    st.session_state[KEY_SEARCH_RAN] = True

if not st.session_state.get(KEY_SEARCH_RAN):
    st.caption("Type a query, or filter by category / tag / source to browse.")
    st.stop()

category = st.session_state.get(KEY_SEARCH_CATEGORY) or ""
tag = st.session_state.get(KEY_SEARCH_TAG) or ""
source = st.session_state.get(KEY_SEARCH_SOURCE) or ""
mode = st.session_state.get("search_mode_input") or "Hybrid"
query = st.session_state.get(KEY_SEARCH_QUERY, "")

if not (query or category or tag or source):
    st.caption("Nothing to search for — enter a query or pick a filter.")
    st.stop()

with st.spinner("Searching your garden…"):
    pagination, warning = _run_search(query, category, tag, source, mode)

if warning:
    st.warning(warning)

total = pagination.total
page = st.session_state[KEY_SEARCH_PAGE]
total_pages = max(1, (total + PER_PAGE_SEARCH - 1) // PER_PAGE_SEARCH)
st.session_state[KEY_SEARCH_PAGE] = min(max(1, page), total_pages)
page = st.session_state[KEY_SEARCH_PAGE]

st.caption(f"{total} result{'s' if total != 1 else ''} for “{query or 'filters'}”")

if not pagination.items:
    st.info("No notes match.")
else:
    for note in pagination.items:
        with st.container(border=True):
            st.markdown(f"**{note.title}**")
            preview = note.content[:220] + ("..." if len(note.content) > 220 else "")
            st.caption(preview)
            badges = []
            if note.category:
                badges.append(note.category)
            badges += [t.name for t in note.tags[:4]]
            if badges:
                st.caption(" · ".join(badges))
            if st.button("Open", key=f"search_open_{note.id}"):
                open_note(note.id)
                try:
                    st.switch_page("streamlit_pages/2_Notes.py")
                except Exception:
                    st.info("Open Notes in the sidebar to view this note.")

    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("← Prev", disabled=page <= 1, use_container_width=True):
            st.session_state[KEY_SEARCH_PAGE] = page - 1
            st.rerun()
    with c2:
        st.caption(f"Page {page} of {total_pages}")
    with c3:
        if st.button("Next →", disabled=page >= total_pages, use_container_width=True):
            st.session_state[KEY_SEARCH_PAGE] = page + 1
            st.rerun()

