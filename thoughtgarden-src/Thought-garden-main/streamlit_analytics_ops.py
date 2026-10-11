"""Dashboard / Insights queries — Streamlit-side port of Flask main routes.

Mirrors app/main/routes.py::dashboard() and ::insights() so the Streamlit
pages show the same numbers the Flask app does. All DB work runs under
streamlit_db.app_context(); business logic stays in app/services/*.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from streamlit_db import app_context


def dashboard_data(user_id: int) -> dict:
    """Stats, lists and panels for the Dashboard page."""
    from app.models import Note, Relationship, Tag, db, note_tags
    from sqlalchemy import func

    with app_context():
        stats = {
            "total_notes": Note.query.filter_by(user_id=user_id).count(),
            "documents": Note.query.filter_by(user_id=user_id)
            .filter(Note.source_type != "manual")
            .count(),
            "connections": Relationship.query.join(
                Note, Relationship.source_note_id == Note.id
            )
            .filter(Note.user_id == user_id)
            .count(),
            "tags": Tag.query.join(note_tags)
            .join(Note)
            .filter(Note.user_id == user_id)
            .distinct()
            .count(),
            "pinned": Note.query.filter_by(user_id=user_id, is_pinned=True).count(),
        }

        recent_notes = (
            Note.query.filter_by(user_id=user_id, is_archived=False)
            .order_by(Note.created_at.desc())
            .limit(5)
            .all()
        )
        _materialize(recent_notes)

        most_connected = (
            db.session.query(Note, func.count(Relationship.id).label("conn_count"))
            .join(
                Relationship,
                (Relationship.source_note_id == Note.id)
                | (Relationship.target_note_id == Note.id),
            )
            .filter(Note.user_id == user_id)
            .group_by(Note.id)
            .order_by(func.count(Relationship.id).desc())
            .limit(5)
            .all()
        )
        for note, _count in most_connected:
            _materialize([note])

        categories = (
            db.session.query(Note.category, func.count(Note.id))
            .filter(Note.user_id == user_id, Note.category.isnot(None))
            .group_by(Note.category)
            .order_by(func.count(Note.id).desc())
            .all()
        )

        orphan_notes = (
            Note.query.filter_by(user_id=user_id, is_archived=False)
            .filter(~Note.relationships.any(), ~Note.inverse_relationships.any())
            .limit(5)
            .all()
        )
        _materialize(orphan_notes)

        rediscover = (
            Note.query.filter_by(user_id=user_id, is_archived=False)
            .order_by(Note.created_at.asc())
            .limit(3)
            .all()
        )
        _materialize(rediscover)

        return {
            "stats": stats,
            "recent_notes": recent_notes,
            "most_connected": [(n, c) for n, c in most_connected],
            "categories": categories,
            "orphan_notes": orphan_notes,
            "rediscover": rediscover,
        }


def insights_data(user_id: int) -> dict:
    """Metrics for the Insights page ({} when the garden is empty)."""
    from app.models import Note, Relationship, db
    from sqlalchemy import func

    with app_context():
        total_notes = Note.query.filter_by(user_id=user_id).count()
        if total_notes == 0:
            return {}

        most_connected_topic = (
            db.session.query(Note.category, func.count(Relationship.id))
            .join(
                Relationship,
                (Relationship.source_note_id == Note.id)
                | (Relationship.target_note_id == Note.id),
            )
            .filter(Note.user_id == user_id, Note.category.isnot(None))
            .group_by(Note.category)
            .order_by(func.count(Relationship.id).desc())
            .first()
        )

        largest_category = (
            db.session.query(Note.category, func.count(Note.id))
            .filter(Note.user_id == user_id, Note.category.isnot(None))
            .group_by(Note.category)
            .order_by(func.count(Note.id).desc())
            .first()
        )

        strongest = (
            Relationship.query.join(Note, Relationship.source_note_id == Note.id)
            .filter(Note.user_id == user_id)
            .order_by(Relationship.similarity_score.desc())
            .first()
        )
        strongest_connection = None
        if strongest is not None:
            source = Note.query.get(strongest.source_note_id)
            target = Note.query.get(strongest.target_note_id)
            strongest_connection = {
                "source": source.title if source else "?",
                "target": target.title if target else "?",
                "score": strongest.similarity_score,
                "type": strongest.relationship_type,
            }

        notes_no_connections = (
            Note.query.filter_by(user_id=user_id, is_archived=False)
            .filter(~Note.relationships.any(), ~Note.inverse_relationships.any())
            .count()
        )

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recently_growing = (
            db.session.query(Note.category, func.count(Note.id))
            .filter(
                Note.user_id == user_id,
                Note.category.isnot(None),
                Note.created_at >= thirty_days_ago,
            )
            .group_by(Note.category)
            .order_by(func.count(Note.id).desc())
            .first()
        )

        return {
            "total_notes": total_notes,
            "most_connected_topic": most_connected_topic,
            "largest_category": largest_category,
            "strongest_connection": strongest_connection,
            "notes_no_connections": notes_no_connections,
            "recently_growing": recently_growing,
        }


def _materialize(notes) -> None:
    """Touch relations/attrs used later so lazy loads happen inside the context."""
    for n in notes:
        _ = list(n.tags)
        _ = n.title, n.content, n.category, n.created_at, n.updated_at, n.is_pinned
