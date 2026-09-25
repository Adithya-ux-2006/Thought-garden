from datetime import datetime, timedelta, timezone

import pytest

from app import create_app, db
from app.models import User, Note, Relationship

pytestmark = pytest.mark.starter_garden

DEMO_EMAIL = 'demo@thoughtgarden.app'


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_seed_demo_creates_demo_garden(app):
    result = app.test_cli_runner().invoke(args=['seed-demo'])

    assert result.exit_code == 0, result.output
    demo = User.query.filter_by(email=DEMO_EMAIL).one()
    assert demo.check_password('demo1234')
    notes = Note.query.filter_by(user_id=demo.id).all()
    assert len(notes) == 17
    assert {n.source_type for n in notes} == {'manual'}
    assert Relationship.query.count() > 0

    hub = next(n for n in notes if n.title == 'Machine Learning Fundamentals')
    assert hub.created_at < datetime.now(timezone.utc) - timedelta(days=19)
    assert DEMO_EMAIL in result.output


def test_seed_demo_is_idempotent(app):
    runner = app.test_cli_runner()
    runner.invoke(args=['seed-demo'])
    counts = (User.query.count(), Note.query.count(), Relationship.query.count())

    result = runner.invoke(args=['seed-demo'])

    assert result.exit_code == 0
    assert 'already exists' in result.output
    assert (User.query.count(), Note.query.count(), Relationship.query.count()) == counts


def test_reindex_rebuilds_relationships(app):
    runner = app.test_cli_runner()
    runner.invoke(args=['seed-demo'])
    expected = Relationship.query.count()
    Relationship.query.delete()
    db.session.commit()

    result = runner.invoke(args=['reindex'])

    assert result.exit_code == 0, result.output
    assert Relationship.query.count() == expected
    assert f'{expected} relationships across 17 notes' in result.output


def test_reindex_on_empty_database(app):
    result = app.test_cli_runner().invoke(args=['reindex'])

    assert result.exit_code == 0, result.output
    assert '0 relationships across 0 notes' in result.output
