"""Single-user password gate (placeholder for Flask-Login).

v1 assumption (confirmed): one local/self-hosted instance, one person.
No register/login multi-user flow. Password comes from STREAMLIT_GATE_PASSWORD
(or st.secrets if present); after unlock we bind to the first User row in DB.
The database starts empty of notes — the garden is built from what the user
types, never from seeded demo data.
"""

from __future__ import annotations

import os

import streamlit as st

from streamlit_state import KEY_AUTH_OK, KEY_GATE_ERROR, KEY_USER_ID, init_state

_DEFAULT_GATE_PASSWORD = "demo1234"  # override via STREAMLIT_GATE_PASSWORD


def _configured_password() -> str:
    # Prefer Streamlit secrets when configured, else env, else local default.
    try:
        secrets = getattr(st, "secrets", None)
        if secrets is not None and "gate_password" in secrets:
            return str(secrets["gate_password"])
    except Exception:
        pass
    return os.environ.get("STREAMLIT_GATE_PASSWORD", _DEFAULT_GATE_PASSWORD)


def is_authenticated() -> bool:
    return bool(st.session_state.get(KEY_AUTH_OK))


def logout() -> None:
    st.session_state[KEY_AUTH_OK] = False
    st.session_state[KEY_USER_ID] = None
    st.session_state[KEY_GATE_ERROR] = None


def current_user_id() -> int | None:
    return st.session_state.get(KEY_USER_ID)


def render_auth_gate() -> None:
    """Full-page password form. Call instead of page body when logged out."""
    st.title("Thought Garden")
    st.caption("Local / single-user access")

    with st.form("gate_login"):
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Enter", use_container_width=True)
        if submitted:
            if password == _configured_password():
                from streamlit_db import resolve_single_user_id

                run_startup_once_safe()
                user_id = resolve_single_user_id()
                if user_id is None:
                    st.session_state[KEY_GATE_ERROR] = (
                        "Could not create the local user. Check the database file."
                    )
                else:
                    st.session_state[KEY_AUTH_OK] = True
                    st.session_state[KEY_USER_ID] = user_id
                    st.session_state[KEY_GATE_ERROR] = None
                    st.rerun()
            else:
                st.session_state[KEY_GATE_ERROR] = "Incorrect password."

    err = st.session_state.get(KEY_GATE_ERROR)
    if err:
        st.error(err)

    st.caption(
        "Placeholder gate — not multi-user auth. "
        "Set `STREAMLIT_GATE_PASSWORD` to change the password."
    )


def run_startup_once_safe() -> None:
    from streamlit_db import run_startup_once

    run_startup_once()


def require_auth() -> bool:
    """Init state; show gate and stop the script if not authenticated.

    Returns True when authenticated (page body may proceed).
    """
    init_state()
    if not is_authenticated():
        render_auth_gate()
        st.stop()
        return False
    return True
