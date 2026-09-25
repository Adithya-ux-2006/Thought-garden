import hashlib
import re

import numpy as np
import pytest
from sqlalchemy import text

from app.services import embedding_service, indexer, onboarding_service

EMBEDDING_DIM = 384


class FakeEmbeddingModel:
    """Deterministic stand-in for SentenceTransformer: hashed bag of words,
    so texts sharing words are more similar. No downloads, no torch."""

    is_test_stub = True

    def encode(self, text, convert_to_numpy=True, normalize_embeddings=True):
        vector = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        vector[0] = 0.1  # keeps empty text from producing a zero vector
        for word in re.findall(r'[a-z0-9]+', text.lower()):
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % (EMBEDDING_DIM - 1) + 1
            vector[bucket] += 1.0
        if normalize_embeddings:
            vector /= np.linalg.norm(vector)
        return vector


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'starter_garden: register new users with the real starter garden')


@pytest.fixture(autouse=True)
def _no_starter_garden_unless_marked(request, monkeypatch):
    # Most tests assume a new account starts empty.
    if 'starter_garden' not in request.keywords:
        monkeypatch.setattr(onboarding_service, 'load_starter_notes', lambda: [], raising=False)


def _ensure_fts_schema():
    # db.create_all() only creates tables from db.metadata - note_fts is a
    # raw-SQL FTS5 virtual table that exists solely in the
    # f2e8b4d6a1c9 migration, so test fixtures that build schema via
    # create_all() (rather than running migrations) never get it or its
    # sync triggers. Mirrors that migration's upgrade() exactly.
    from app import db

    existing = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='note_fts'")
    ).fetchone()
    if existing:
        return
    db.session.execute(text("""
        CREATE VIRTUAL TABLE note_fts USING fts5(
            title, content, content='note', content_rowid='id'
        )
    """))
    db.session.execute(text("""
        CREATE TRIGGER note_fts_ai AFTER INSERT ON note BEGIN
            INSERT INTO note_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
        END
    """))
    db.session.execute(text("""
        CREATE TRIGGER note_fts_ad AFTER DELETE ON note BEGIN
            INSERT INTO note_fts(note_fts, rowid, title, content) VALUES ('delete', old.id, old.title, old.content);
        END
    """))
    db.session.execute(text("""
        CREATE TRIGGER note_fts_au AFTER UPDATE ON note BEGIN
            INSERT INTO note_fts(note_fts, rowid, title, content) VALUES ('delete', old.id, old.title, old.content);
            INSERT INTO note_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
        END
    """))
    db.session.commit()


@pytest.fixture(autouse=True)
def _sync_fts_schema_after_create_all(monkeypatch):
    # Wrapping create_all (rather than editing every test file's own `app`
    # fixture) keeps this fix in one place and covers any fixture that
    # calls db.create_all() directly.
    from app import db

    original_create_all = db.create_all

    def wrapped(*args, **kwargs):
        original_create_all(*args, **kwargs)
        if db.engine.url.get_backend_name() == 'sqlite':
            _ensure_fts_schema()

    monkeypatch.setattr(db, 'create_all', wrapped)
    yield


@pytest.fixture(autouse=True)
def _stub_ml_and_threads(monkeypatch):
    # The real worker thread is never started under pytest (create_app()
    # gates start_worker() on `not TESTING`); tests call
    # indexer.process_pending(app) directly instead. Stubbing the model and
    # `ready` here makes that call behave as if the worker had already
    # loaded a model, without downloading one or spawning a thread.
    monkeypatch.setattr(embedding_service, '_model', FakeEmbeddingModel())
    monkeypatch.setattr(indexer, 'ready', True)
    yield
