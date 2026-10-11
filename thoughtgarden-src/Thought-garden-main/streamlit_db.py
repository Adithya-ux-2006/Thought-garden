"""Streamlit-side DB/app bootstrap.

Wraps the existing Flask create_app() so Streamlit pages can run queries
under an app context without starting the Flask server. Startup side
effects (first-run user creation, relationship backfill) are guarded to
run once per process via streamlit_db.run_startup_once()'s lru_cache.

No demo/seed notes are ever written: the garden is built from user input
only. seed.py stays available for the Flask dev server but Streamlit
never calls it.
"""

from __future__ import annotations

import secrets
from contextlib import contextmanager
from functools import lru_cache


@lru_cache(maxsize=1)
def get_flask_app():
    """Create (and memoize) the Flask app used only as a DB/config host.

    Never call app.run() from Streamlit — this process is Streamlit's.
    """
    from app import create_app

    return create_app()


@contextmanager
def app_context():
    app = get_flask_app()
    with app.app_context():
        yield app


def ensure_local_user() -> int:
    """Create the single local user on first run (no demo notes attached).

    Returns the id of the first user row, creating one if the database is
    brand new. The account exists only so rows can carry a user_id — the
    Streamlit gate (streamlit_auth) is what actually locks the app, and the
    password here is random and never used.
    """
    from app import db
    from app.models import User

    with app_context():
        user = User.query.order_by(User.id.asc()).first()
        if user is None:
            user = User(
                name="You",
                email="local@thoughtgarden.local",
            )
            user.set_password(secrets.token_urlsafe(24))
            db.session.add(user)
            db.session.commit()
        return user.id


@lru_cache(maxsize=1)
def run_startup_once() -> dict:
    """Idempotent process-level startup: create local user, backfill links.

    Mirrors run.py's duties minus the demo seeding — this instance starts
    with an empty garden and grows only from user input. Relationship
    generation is automatic: ensure_all_relationships() scores every
    existing pair once at startup, and each save re-scores its own note.
    Runs at most once per Streamlit process (lru_cache survives script
    reruns; cleared only on full server restart).
    """
    get_flask_app()  # ensure create_all has run
    ensure_local_user()

    with app_context():
        from app.services.similarity_service import ensure_all_relationships

        note_count, connection_count = ensure_all_relationships()

    return {
        "note_count": note_count,
        "connection_count": connection_count,
        "relationships_ready": True,
    }


def resolve_single_user_id() -> int | None:
    """Single-user Streamlit: bind session to the first User row.

    ensure_local_user() makes that row exist on a brand-new database, so
    an unlocked gate always has something to bind to.
    """
    ensure_local_user()
    with app_context():
        from app.models import User

        user = User.query.order_by(User.id.asc()).first()
        return user.id if user else None
