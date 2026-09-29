"""Profile — edit name/email, change password, sign out.

Port of Flask auth.profile(): same rules (changing password requires the
current one; name/email save together). Adds a short garden summary since
the Streamlit port has no other account page.
"""

from __future__ import annotations

import streamlit as st

from streamlit_auth import current_user_id, logout, require_auth

st.set_page_config(page_title="Profile · Thought Garden", page_icon="👤", layout="wide")
require_auth()

uid = current_user_id()
if uid is None:
    st.error("No session user.")
    st.stop()

from streamlit_analytics_ops import dashboard_data
from streamlit_db import app_context

with app_context():
    from app import db
    from app.models import User

    user = db.session.get(User, uid)
    if user is None:
        st.error("Session user no longer exists.")
        st.stop()

    st.title("Profile")

    stats = dashboard_data(uid)["stats"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Notes", stats["total_notes"])
    m2.metric("Connections", stats["connections"])
    m3.metric("Tags", stats["tags"])
    m4.metric("Documents", stats["documents"])

    st.divider()

    left, right = st.columns([3, 2])

    with left:
        st.subheader("Account")
        with st.form("profile_form"):
            name = st.text_input("Name", value=user.name or "")
            email = st.text_input("Email", value=user.email or "")
            st.caption("Changing your password needs your current one.")
            c1, c2 = st.columns(2)
            with c1:
                current_password = st.text_input("Current password", type="password")
            with c2:
                new_password = st.text_input("New password", type="password")
            saved = st.form_submit_button("Save profile", type="primary")

        if saved:
            error = None
            if current_password or new_password:
                if not current_password:
                    error = "Enter your current password to change it."
                elif not user.check_password(current_password):
                    error = "Current password is incorrect."
                elif new_password and len(new_password) < 6:
                    error = "New password needs at least 6 characters."

            if error:
                st.error(error)
            else:
                user.name = (name or "").strip() or user.name
                user.email = (email or "").strip() or user.email
                if current_password and new_password:
                    user.set_password(new_password)
                db.session.commit()
                st.success("Profile updated.")

    with right:
        st.subheader("Session")
        st.caption(
            "This copy of Thought Garden runs as a single local user — the "
            "garden lives in the local database file, no account to create."
        )
        if st.button("Log out", use_container_width=True):
            logout()
            st.rerun()
