import pytest
from sqlalchemy import text

from app import create_app, db
from app.models import Note, User
from app.services import indexer, search_service


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def user(app):
    u = User(name='Test User', email='test@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


def _note(user_id, title, content, **fields):
    note = Note(user_id=user_id, title=title, content=content, **fields)
    db.session.add(note)
    db.session.commit()
    return note


def _fts_rowids():
    return {row[0] for row in db.session.execute(text('SELECT rowid FROM note_fts')).fetchall()}


# ---- trigger-based insert/update/delete synchronization ----

def test_insert_note_is_indexed_in_fts(app, user):
    note = _note(user.id, 'Zebra Habits', 'Notes about zebra stripes.')

    assert note.id in _fts_rowids()
    results = search_service.keyword_search(user.id, 'zebra')
    assert [n.title for n in results.items] == ['Zebra Habits']


def test_update_note_resyncs_fts(app, user):
    note = _note(user.id, 'Original Title', 'Original content about gardens.')

    note.title = 'Renamed Title'
    note.content = 'Completely different content about rivers.'
    db.session.commit()

    assert search_service.keyword_search(user.id, 'gardens').items == []
    rivers_results = search_service.keyword_search(user.id, 'rivers').items
    assert len(rivers_results) == 1
    assert rivers_results[0].id == note.id


def test_delete_note_removes_from_fts(app, user):
    note = _note(user.id, 'Temporary', 'Content to be deleted.')
    note_id = note.id

    db.session.delete(note)
    db.session.commit()

    assert note_id not in _fts_rowids()
    assert search_service.keyword_search(user.id, 'temporary').items == []


# ---- bm25() ranking ----

def test_bm25_ranks_denser_match_first(app, user):
    _note(user.id, 'Sparse mention', 'apples oranges pears grapes plums melons '
          'berries mango kiwi lemon lime coconut machine papaya fig date.')
    _note(user.id, 'Dense mention', 'machine machine machine machine short note.')

    results = search_service.keyword_search(user.id, 'machine')
    assert [n.title for n in results.items][0] == 'Dense mention'


# ---- snippet() highlighting ----

def test_snippet_highlights_match_and_escapes_html(app, user):
    _note(user.id, 'XSS test', '<script>alert(1)</script> zebra rides a bicycle in the evening.')

    results = search_service.keyword_search(user.id, 'zebra')
    snippet = str(results.items[0].snippet)

    assert '<mark>zebra</mark>' in snippet.lower()
    assert '<script>' not in snippet
    assert '&lt;script&gt;' in snippet


def test_search_query_operator_word_is_treated_literally(app, user):
    _note(user.id, 'Fruit note', 'apples or oranges for the discussion.')

    results = search_service.keyword_search(user.id, 'or')
    assert [n.title for n in results.items] == ['Fruit note']


# ---- hybrid FTS + vector retrieval via RRF, gated on indexer.ready ----

def test_hybrid_search_skips_semantic_when_indexer_not_ready(app, user, monkeypatch):
    note = _note(user.id, 'Cats and dogs', 'Cats and dogs are common household pets.')
    calls = []
    monkeypatch.setattr(search_service, 'semantic_search',
                         lambda *a, **k: calls.append(1) or search_service.SimplePagination([], 1, 10, 0))
    monkeypatch.setattr(indexer, 'ready', False)

    results = search_service.hybrid_search(user.id, 'cats')

    assert calls == []
    assert any(n.id == note.id for n in results.items)


def test_hybrid_search_uses_semantic_when_indexer_ready(app, user, monkeypatch):
    _note(user.id, 'Cats and dogs', 'Cats and dogs are common household pets.')
    calls = []
    monkeypatch.setattr(search_service, 'semantic_search',
                         lambda *a, **k: calls.append(1) or search_service.SimplePagination([], 1, 10, 0))
    monkeypatch.setattr(indexer, 'ready', True)

    search_service.hybrid_search(user.id, 'cats')

    assert calls == [1]
