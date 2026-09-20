from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from app import create_app, db
from app.models import Note, Relationship, User
from app.services.note_lifecycle_service import (
    create_manual_note,
    import_notes_from_file,
    update_manual_note,
)


@pytest.fixture
def app():
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


def test_lifecycle_persists_then_connects_and_imports(app):
    with app.app_context():
        user = User(name='Lifecycle User', email='lifecycle@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        first = create_manual_note(
            user.id,
            title='Machine Learning Basics',
            content='Machine learning uses data for learning patterns.',
            category='AI',
            tags='AI, learning',
            is_pinned=True,
        ).notes[0]
        assert first.id is not None
        assert first.is_pinned is True
        assert Relationship.query.count() == 0

        second = create_manual_note(
            user.id,
            title='Neural Learning',
            content='Neural networks learn patterns from data.',
            category='AI',
            tags='AI, learning',
        ).notes[0]
        assert Relationship.query.count() == 1
        relationship = Relationship.query.one()
        assert {relationship.source_note_id, relationship.target_note_id} == {first.id, second.id}

        update_manual_note(
            first,
            title='Machine Learning Overview',
            content='Machine learning creates patterns from data.',
            category='Research',
            tags='AI, research',
        )
        refreshed = db.session.get(Note, first.id)
        assert refreshed.category == 'Research'
        assert {tag.name for tag in refreshed.tags} == {'AI', 'research'}

        upload = FileStorage(
            stream=BytesIO(b'Knowledge graphs connect related ideas.'),
            filename='knowledge.txt',
        )
        imported = import_notes_from_file(user.id, upload, category='AI').notes
        assert len(imported) == 1
        assert imported[0].source_type == 'txt'
        assert Note.query.filter_by(user_id=user.id).count() == 3
