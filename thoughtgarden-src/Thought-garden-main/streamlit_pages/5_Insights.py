"""Insights — garden metrics (port of Flask main/insights)."""

from __future__ import annotations

import streamlit as st

from streamlit_analytics_ops import insights_data
from streamlit_auth import current_user_id, require_auth

st.set_page_config(page_title="Insights · Thought Garden", page_icon="📈", layout="wide")
require_auth()

user_id = current_user_id()
if user_id is None:
    st.error("No session user.")
    st.stop()

st.title("Insights")

insights = insights_data(user_id)

if not insights:
    st.info("Nothing to analyze yet — add a few notes and connections first.")
    st.stop()

topic = insights.get("most_connected_topic")
largest = insights.get("largest_category")
growing = insights.get("recently_growing")
strongest = insights.get("strongest_connection")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total notes", insights["total_notes"])
with c2:
    st.metric("Notes without connections", insights["notes_no_connections"])
with c3:
    st.metric(
        "Strongest connection",
        f"{strongest['score']:.0%}" if strongest else "—",
    )

st.divider()

if topic:
    st.subheader("Most connected topic")
    st.write(f"**{topic[0]}** — {topic[1]} connection{'s' if topic[1] != 1 else ''}.")

if largest:
    st.subheader("Largest category")
    st.write(f"**{largest[0]}** — {largest[1]} note{'s' if largest[1] != 1 else ''}.")

if growing:
    st.subheader("Growing topic (last 30 days)")
    st.write(f"**{growing[0]}** — {growing[1]} new note{'s' if growing[1] != 1 else ''}.")

if strongest:
    st.subheader("Strongest connection")
    st.write(
        f"**{strongest['source']}** ↔ **{strongest['target']}** — "
        f"{strongest['score']:.0%} ({strongest['type']})."
    )

if insights["notes_no_connections"]:
    st.subheader("Needs attention")
    st.warning(
        f"{insights['notes_no_connections']} note"
        f"{'s have' if insights['notes_no_connections'] != 1 else ' has'} no "
        "connections yet. Connections are generated automatically after each "
        "save — keep writing and they'll link up."
    )
