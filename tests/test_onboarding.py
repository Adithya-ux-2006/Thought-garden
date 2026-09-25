import json
import os

import pytest

from app import create_app, db
from app.forms import NoteForm
from app.models import User, Note, Tag, Relationship

FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'app', 'data', 'starter_notes.json')

pytestmark = pytest.mark.starter_garden


def _fixture():
    with open(FIXTURE, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False, 'SECRET_KEY': 'test-secret-key',
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _register(client, email='new@example.com'):
    return client.post('/auth/register', data={
        'name': 'New User', 'email': email,
        'password': 'password123', 'confirm_password': 'password123',
    })


def test_starter_fixture_is_well_formed():
    notes = _fixture()
    preset_categories = {value for value, _ in NoteForm.category.kwargs['choices']}
    assert len(notes) == 17
    for note in notes:
        assert note['title'] and note['content']
        assert note['category'] in preset_categories
        assert all(0 < len(tag) <= 50 for tag in note['tags'])


def test_new_user_gets_starter_garden_without_demo_account(app):
    response = _register(app.test_client())

    assert response.headers['Location'] == '/garden/'
    user = User.query.filter_by(email='new@example.com').one()
    notes = Note.query.filter_by(user_id=user.id).all()
    assert sorted(n.title for n in notes) == sorted(n['title'] for n in _fixture())
    assert {n.source_type for n in notes} == {'starter'}

    expected = {n['title']: set(n['tags']) for n in _fixture()}
    assert all({t.name for t in n.tags} == expected[n.title] for n in notes)

    note_ids = [n.id for n in notes]
    assert Relationship.query.filter(Relationship.source_note_id.in_(note_ids)).count() > 0


def test_starter_garden_never_copies_demo_account_content(app):
    demo = User(name='Demo', email='demo@thoughtgarden.app')
    demo.set_password('demo1234')
    db.session.add(demo)
    db.session.flush()
    injected = Note(user_id=demo.id, title='INJECTED', content='Edited by someone with the demo password.')
    injected.tags.append(Tag(user_id=demo.id, name='<img src=x onerror=alert(1)>'))
    db.session.add(injected)
    db.session.commit()

    _register(app.test_client())

    user = User.query.filter_by(email='new@example.com').one()
    notes = Note.query.filter_by(user_id=user.id).all()
    assert 'INJECTED' not in {n.title for n in notes}
    assert all('<img' not in t.name for n in notes for t in n.tags)
    assert len(notes) == len(_fixture())
