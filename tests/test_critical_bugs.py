import re

import pytest

from app import create_app, db
from app.models import User, Note, Tag
from app.services.pagination import SimplePagination


def _no_semantic_results(user_id, query, *args, page=1, per_page=10, **kwargs):
    return SimplePagination([], page, per_page, 0)


@pytest.fixture
def app(monkeypatch):
    # Keep these tests off the ML model: they exercise routing/forms/queries,
    # not embeddings. indexer.enqueue() itself never touches the model (it
    # only writes an index_job row), so it's left real.
    monkeypatch.setattr('app.services.search_service.semantic_search', _no_semantic_results)
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
def client(app):
    client = app.test_client()
    client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
    })
    return client


def _user_id():
    return User.query.filter_by(email='test@example.com').one().id


def _add_note(title, content='Some content.', tags=(), **fields):
    note = Note(user_id=_user_id(), title=title, content=content, **fields)
    for name in tags:
        tag = Tag.query.filter_by(user_id=_user_id(), name=name).first() or Tag(user_id=_user_id(), name=name)
        note.tags.append(tag)
    db.session.add(note)
    db.session.commit()
    return note.id


# ---- C1: search form field must reach the search route ----

def test_search_form_query_field_reaches_search_route(client):
    _add_note('Zebra habits', content='Notes about zebra stripes.')

    page = client.get('/search/').data.decode()
    text_inputs = re.findall(r'<input[^>]*type="text"[^>]*>', page)
    assert len(text_inputs) == 1
    field_name = re.search(r'name="([^"]+)"', text_inputs[0]).group(1)

    response = client.get(f'/search/?{field_name}=zebra')
    assert b'Zebra habits' in response.data


# ---- C2: editing a note must save the submitted tags ----

def test_edit_note_saves_changed_tags(client):
    note_id = _add_note('Tagged', tags=['old'])

    client.post(f'/notes/{note_id}/edit', data={
        'title': 'Tagged', 'content': 'Some content.', 'tags': 'new, fresh',
    })

    note = db.session.get(Note, note_id)
    assert {t.name for t in note.tags} == {'new', 'fresh'}


def test_edit_form_prefills_existing_tags(client):
    note_id = _add_note('Tagged', tags=['alpha'])

    page = client.get(f'/notes/{note_id}/edit').data.decode()
    tags_input = re.search(r'<input[^>]*name="tags"[^>]*>', page).group(0)
    assert 'value="alpha"' in tags_input


# ---- C3: importing a multi-chunk document must complete ----

def test_import_long_text_document_creates_multiple_notes(client):
    import io
    body = ('Paragraph about gardens and knowledge graphs. ' * 120).encode()
    assert len(body) > 5000

    response = client.post('/notes/import', data={
        'file': (io.BytesIO(body), 'long.txt'),
    }, content_type='multipart/form-data')

    assert response.status_code == 302
    notes = Note.query.filter_by(source_filename='long.txt').all()
    assert len(notes) >= 3
    assert all(n.source_type == 'txt' for n in notes)


# ---- C4: source filter options must match stored source_type values ----

@pytest.mark.parametrize('label, stored', [('Markdown', 'md'), ('Text', 'txt'), ('PDF', 'pdf')])
def test_search_source_filter_matches_imported_notes(client, label, stored):
    _add_note(f'Imported {stored} note', source_type=stored, source_filename=f'doc.{stored}')

    page = client.get('/search/').data.decode()
    value = re.search(rf'<option[^>]*value="([^"]*)"[^>]*>{label}</option>', page).group(1)

    response = client.get(f'/search/?source_type={value}')
    assert f'Imported {stored} note'.encode() in response.data


# ---- C5: result count must be the total, not the page size ----

def test_search_result_count_reports_total_matches(client):
    for i in range(12):
        _add_note(f'AI note {i}', category='AI')

    response = client.get('/search/?category=AI')
    assert b'Found 12 results' in response.data


# ---- C7: dashboard stats must ignore archived notes; documents = imports ----

def test_dashboard_stats_exclude_archived_and_starter_notes(client):
    _add_note('Active manual', is_pinned=True, tags=['live'])
    _add_note('Archived manual', is_pinned=True, is_archived=True, tags=['ghost'])
    _add_note('Starter copy', source_type='starter')
    _add_note('Imported pdf', source_type='pdf', source_filename='a.pdf')
    _add_note('Archived md', source_type='md', source_filename='b.md', is_archived=True)

    page = client.get('/dashboard').data.decode()
    total, documents, _connections, tags, pinned = [
        int(n) for n in re.findall(r'class="stat-number">(\d+)<', page)
    ]
    assert total == 3
    assert documents == 1
    assert tags == 1
    assert pinned == 1


# ---- C8: suggestions must not include archived notes ----

def test_suggest_excludes_archived_notes(client):
    _add_note('Zebra active')
    _add_note('Zebra archived', is_archived=True)

    titles = {s['title'] for s in client.get('/search/api/suggest?q=zebra').get_json()}
    assert titles == {'Zebra active'}


# ---- C9: editing a note whose category isn't a preset choice ----

def test_edit_form_keeps_non_preset_category_selected(client):
    note_id = _add_note('Custom category', category='Philosophy')

    page = client.get(f'/notes/{note_id}/edit').data.decode()
    assert re.search(r'<option[^>]*selected[^>]*value="Philosophy"', page)


def test_edit_note_with_non_preset_category_saves(client):
    note_id = _add_note('Custom category', category='Philosophy')

    response = client.post(f'/notes/{note_id}/edit', data={
        'title': 'Renamed', 'content': 'Some content.', 'category': 'Philosophy', 'tags': '',
    })

    assert response.status_code == 302
    note = db.session.get(Note, note_id)
    assert note.title == 'Renamed'
    assert note.category == 'Philosophy'


def test_edit_note_accepts_a_brand_new_unlisted_category(client):
    # Durable fix: category is free text with presets, not a real enum (see
    # app/services/category_service.py + NoteForm's validate_choice=False),
    # so switching to *any* string - not just one the note already had -
    # must succeed, not 200-with-errors like the old choice-patching hack
    # that only special-cased the note's pre-existing value.
    note_id = _add_note('Custom category', category='Philosophy')

    response = client.post(f'/notes/{note_id}/edit', data={
        'title': 'Renamed', 'content': 'Some content.', 'category': 'Anything Else', 'tags': '',
    })

    assert response.status_code == 302
    note = db.session.get(Note, note_id)
    assert note.title == 'Renamed'
    assert note.category == 'Anything Else'
