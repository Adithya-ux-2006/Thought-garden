"""Streamlit adapter for background embedding generation.

Caller-facing API takes only note_id (no Flask request/app argument).
The worker still enters the singleton Flask app context created by
streamlit_db.get_flask_app() — required for Flask-SQLAlchemy — but page
code never has to pass an app through.

Do NOT wrap this function in @st.cache_resource: it starts a new daemon
thread per save. Cache the model loader instead (see warm_embedding_model).
"""

from __future__ import annotations

import threading


def queue_embedding_generation_streamlit(note_id: int) -> None:
    """Fire-and-forget: generate embedding + rescoring for note_id."""
    from streamlit_db import get_flask_app

    app = get_flask_app()

    def _work():
        with app.app_context():
            from app.models import Note
            from app.services.embedding_service import generate_embedding
            from app.services.similarity_service import update_relationships_for_note

            note = db_get(Note, note_id)
            if note is None:
                return
            try:
                generate_embedding(note)
                update_relationships_for_note(note)
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Background embedding generation failed for note %s", note_id
                )

    def db_get(model, pk):
        from app import db

        return db.session.get(model, pk)

    threading.Thread(target=_work, daemon=True).start()


def warm_embedding_model():
    """Load sentence-transformers once per process under st.cache_resource.

    embedding_service.get_model() already memoizes in a module global;
    this wrapper makes that load explicit to Streamlit's cache lifecycle
    and avoids re-entering get_model() ad hoc from multiple pages.
    """
    import streamlit as st

    @st.cache_resource(show_spinner=False)
    def _cached_model():
        from app.services.embedding_service import get_model

        return get_model()

    return _cached_model()
