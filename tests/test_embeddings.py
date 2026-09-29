import os
import pickle

import numpy as np
import pytest
from flask_migrate import upgrade
from sqlalchemy import text

from app import create_app, db
from app.models import User, Note, NoteEmbedding
from app.services.embedding_service import get_embedding

MIGRATIONS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations'))
EMAIL_REVISION = 'b3c9e1f2a7d4'


@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                      'SECRET_KEY': 'test-secret-key'})
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def no_unpickling(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError('database content must never be unpickled')
    monkeypatch.setattr(pickle, 'loads', refuse)


def _note_with_blob(blob):
    user = User(name='U', email='u@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.flush()
    note = Note(user_id=user.id, title='Legacy', content='Old embedding format.')
    db.session.add(note)
    db.session.flush()
    db.session.add(NoteEmbedding(note_id=note.id, embedding=blob))
    db.session.commit()
    return note.id


@pytest.mark.parametrize('blob', [
    pickle.dumps(np.ones(4, dtype=np.float32)),
    b'\x01\x02\x03',
], ids=['legacy-pickle', 'truncated'])
def test_unreadable_embedding_blob_is_treated_as_missing(app, no_unpickling, blob):
    note_id = _note_with_blob(blob)
    assert get_embedding(note_id, generate_if_missing=False) is None


def test_unreadable_embedding_blob_is_regenerated_as_raw_float32(app, no_unpickling):
    note_id = _note_with_blob(pickle.dumps(np.ones(4, dtype=np.float32)))

    embedding = get_embedding(note_id, generate_if_missing=True)

    stored = db.session.get(NoteEmbedding, note_id).embedding
    assert stored[:1] != b'\x80'
    assert np.allclose(np.frombuffer(stored, dtype=np.float32), embedding)


def test_upgrade_deletes_legacy_pickled_embeddings(tmp_path):
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-key',
                      'SQLALCHEMY_DATABASE_URI': f'sqlite:///{(tmp_path / "e.db").as_posix()}'})
    raw = np.ones(4, dtype=np.float32).tobytes()
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision=EMAIL_REVISION)
        with db.engine.begin() as conn:
            conn.execute(text("INSERT INTO user (id, name, email, password_hash) VALUES (1, 'U', 'u@e.com', 'x')"))
            conn.execute(text("INSERT INTO note (id, user_id, title, content) VALUES (1, 1, 'a', 'a'), (2, 1, 'b', 'b')"))
            conn.execute(text('INSERT INTO note_embeddings (note_id, embedding) VALUES (1, :p), (2, :r)'),
                         {'p': pickle.dumps(np.ones(4, dtype=np.float32)), 'r': raw})

        upgrade(directory=MIGRATIONS)

        with db.engine.connect() as conn:
            rows = conn.execute(text('SELECT note_id, embedding FROM note_embeddings')).fetchall()
        assert rows == [(2, raw)]
        db.engine.dispose()
