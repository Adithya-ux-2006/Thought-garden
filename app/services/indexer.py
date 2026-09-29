"""Background indexer: a single worker thread that owns the embedding
model and keeps every note's embedding, and the relationship graph built
from it, up to date.

Request handlers never touch the model. Saving a note (notes/routes.py,
document_service.py, onboarding_service.py) only ever calls enqueue(note)
- a fast DB write - plus a synchronous rebuild_user_graph() call for
immediate keyword-tier connections. The slower embedding pass, and the
upgrade from keyword-tier to embedding-tier relationships, happens here
once the worker gets to it.

This is one persistent thread, not a thread per save: it is started once
(see start_worker(), called from create_app()) and loops, waking whenever
enqueue() signals new work or its poll interval elapses.
"""

import logging
import threading

from sqlalchemy.exc import IntegrityError

from app import db
from app.models import IndexJob, Note
from app.services import embedding_service
from app.services.similarity_service import rebuild_user_graph
from config import Config

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = Config.INDEXER_POLL_INTERVAL_SECONDS
MAX_ATTEMPTS = Config.INDEX_JOB_MAX_ATTEMPTS

# True once the worker has confirmed a model is loaded. On a machine with
# no network/model access it stays False for the life of the process -
# search and relationship-building then run in keyword-only fallback mode
# instead of failing outright.
ready = False

_worker_thread = None
_stop_event = threading.Event()
_wake_event = threading.Event()


def enqueue(note):
    """Queue `note` for (re-)embedding.

    Fast and request-thread-safe: only writes to index_job, never touches
    the model. A no-op if the note's embedding-relevant text (see
    embedding_service.get_embedding_text) hasn't actually changed since it
    was last embedded, so e.g. toggling pinned doesn't trigger a pointless
    re-embed.
    """
    new_hash = embedding_service.content_hash(note)

    existing_embedding = note.embedding_row
    if existing_embedding is not None and existing_embedding.content_hash == new_hash:
        return

    job = IndexJob.query.filter_by(note_id=note.id).first()
    if job is None:
        job = IndexJob(note_id=note.id, content_hash=new_hash, status='pending', attempts=0)
        db.session.add(job)
    else:
        job.content_hash = new_hash
        job.status = 'pending'
        job.attempts = 0

    try:
        db.session.commit()
    except IntegrityError:
        # Another request thread inserted a job for this note between our
        # SELECT and INSERT (unique note_id) - update its row instead of
        # failing the note save over a benign race.
        db.session.rollback()
        job = IndexJob.query.filter_by(note_id=note.id).first()
        if job is not None:
            job.content_hash = new_hash
            job.status = 'pending'
            job.attempts = 0
            db.session.commit()

    _wake_event.set()


def process_pending(app):
    """Process every currently pending job to completion, then rebuild the
    graph once per distinct user touched (never mid-batch: a bulk import
    enqueuing ten notes for the same user gets one rebuild, not ten).

    Safe to call directly - from `flask reindex`, or from tests - as well
    as from the worker loop; it doesn't start or require a background
    thread itself.
    """
    with app.app_context():
        jobs = IndexJob.query.filter_by(status='pending').all()
        touched_users = set()

        for job in jobs:
            note = db.session.get(Note, job.note_id)
            if note is None:
                db.session.delete(job)
                db.session.commit()
                continue

            try:
                if ready:
                    embedding_service.generate_embedding(note)
                    job.model_version = Config.EMBEDDING_MODEL
                job.status = 'done'
                job.attempts = 0
            except Exception:
                job.attempts += 1
                job.status = 'failed' if job.attempts >= MAX_ATTEMPTS else 'pending'
                logger.exception('Indexing failed for note %s', job.note_id)
            db.session.commit()
            touched_users.add(note.user_id)

        for user_id in touched_users:
            rebuild_user_graph(user_id)


def _load_model(app):
    global ready
    with app.app_context():
        try:
            embedding_service.get_model()
            ready = True
        except Exception:
            ready = False
            logger.exception(
                'Embedding model failed to load - running keyword-only fallback for this process.'
            )


def _run(app):
    _load_model(app)
    while not _stop_event.is_set():
        process_pending(app)
        _wake_event.wait(timeout=POLL_INTERVAL_SECONDS)
        _wake_event.clear()


def start_worker(app):
    """Start the single background indexer thread. Idempotent - calling it
    again while a worker is already running does nothing. The model is
    loaded here, once, before the loop starts processing jobs; nothing on
    a request thread ever calls get_model()."""
    global _worker_thread
    if _worker_thread is not None and _worker_thread.is_alive():
        return

    _stop_event.clear()
    _worker_thread = threading.Thread(target=_run, args=(app,), daemon=True)
    _worker_thread.start()


def stop_worker(timeout=5):
    """Stop the worker thread and wait for it to exit. Mainly for tests
    that start a real worker and need clean teardown instead of a leaked
    daemon thread."""
    global _worker_thread
    _stop_event.set()
    _wake_event.set()
    if _worker_thread is not None:
        _worker_thread.join(timeout=timeout)
    _worker_thread = None
