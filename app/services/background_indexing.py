"""Generate a note's embedding off the request thread.

Previously the semantic (embedding-based) similarity tier only ever
activated the first time a user ran a semantic search - nothing in the
normal create/edit flow ever called generate_embedding(). Until that
first search, every relationship in the graph was keyword-overlap only,
regardless of what the README/docs claim about the app's AI features.

update_relationships_for_note() deliberately never generates embeddings
inline (see similarity_service.py) because that means loading and
running the ML model, which is too slow to do inside a request/response
cycle. This module runs that same work in a background thread instead,
so a note save stays fast but the embedding - and the real semantic
relationships built from it - show up shortly after, without needing
anyone to run a search first.

This is a lightweight stand-in for a proper task queue (Celery/RQ). For
a project this size a background thread per save is a reasonable
trade-off; if usage ever grows past a handful of concurrent users, this
is the first thing to replace with a real job queue.
"""

import threading


def queue_embedding_generation(app, note_id):
    """Fire-and-forget: generate the given note's embedding, then
    recompute its relationships now that a real embedding exists to
    compare against. Runs in its own thread so the caller (a Flask
    request handler) can return immediately.
    """
    def _work():
        with app.app_context():
            from app import db
            from app.models import Note
            from app.services.embedding_service import generate_embedding
            from app.services.similarity_service import update_relationships_for_note

            note = db.session.get(Note, note_id)
            if note is None:
                return
            try:
                generate_embedding(note)
                update_relationships_for_note(note)
            except Exception:
                # Best-effort background work: a failure here (e.g. the
                # model can't be downloaded because there's no network)
                # should never surface to the user who already got their
                # "note saved" response. The keyword-overlap relationships
                # computed synchronously at save time still stand.
                app.logger.exception(
                    'Background embedding generation failed for note %s', note_id
                )

    thread = threading.Thread(target=_work, daemon=True)
    thread.start()
