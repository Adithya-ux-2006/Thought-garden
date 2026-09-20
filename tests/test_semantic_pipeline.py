import pytest

from app import create_app, db
from app.models import Note, Relationship, SemanticJob, User


@pytest.fixture
def app():
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'pipeline-test',
    })
    with application.app_context():
        user = User(name='Pipeline User', email='pipeline@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_client(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True
    return client


def test_note_only_input_runs_complete_pipeline(app, auth_client):
    for content in (
        'Machine learning models discover patterns in research data.',
        'Neural machine learning uses data to train intelligent models.',
    ):
        response = auth_client.post('/notes/create', data={
            'title': '', 'content': content, 'category': '', 'tags': '',
        })
        assert response.status_code == 302
        assert '/garden/' in response.headers['Location']

    with app.app_context():
        notes = Note.query.filter_by(user_id=1).order_by(Note.id).all()
        created = notes[-2:]
        assert all(note.title for note in created)
        assert all(note.category == 'AI' for note in created)
        assert all(note.tags for note in created)
        assert SemanticJob.query.filter_by(status='completed').count() >= 2
        assert Relationship.query.count() >= 1
