from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import Note, Tag, User
from app.services import category_service, tag_service


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _user(email):
    user = User(name='U', email=email)
    user.set_password('password123')
    db.session.add(user)
    db.session.flush()
    return user


# ---- Tag: per-user uniqueness ----

def test_same_tag_name_is_allowed_across_different_users(app):
    a = _user('a@example.com')
    b = _user('b@example.com')
    db.session.add_all([Tag(user_id=a.id, name='AI'), Tag(user_id=b.id, name='AI')])
    db.session.commit()

    assert Tag.query.count() == 2


def test_duplicate_exact_tag_name_within_one_user_is_rejected(app):
    user = _user('a@example.com')
    db.session.add(Tag(user_id=user.id, name='AI'))
    db.session.commit()

    db.session.add(Tag(user_id=user.id, name='AI'))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_case_insensitive_duplicate_tag_within_one_user_is_rejected(app):
    user = _user('a@example.com')
    db.session.add(Tag(user_id=user.id, name='AI'))
    db.session.commit()

    db.session.add(Tag(user_id=user.id, name='ai'))
    with pytest.raises(IntegrityError):
        db.session.commit()


# ---- Note.summary removal ----

def test_note_has_no_summary_column(app):
    assert 'summary' not in Note.__table__.columns


# ---- UTCDateTime round-trips as aware UTC ----

def test_note_created_at_round_trips_as_aware_utc(app):
    user = _user('a@example.com')
    note = Note(user_id=user.id, title='T', content='C')
    db.session.add(note)
    db.session.commit()
    db.session.expire(note)

    assert note.created_at.tzinfo == timezone.utc


def test_naive_datetime_assigned_to_created_at_is_stored_as_utc(app):
    # Note.created_at is UTCDateTime, which must accept a naive input
    # (treated as already-UTC) without raising, then read back aware.
    user = _user('a@example.com')
    note = Note(user_id=user.id, title='T', content='C',
                created_at=datetime(2026, 1, 1, 12, 0, 0))
    db.session.add(note)
    db.session.commit()
    db.session.expire(note)

    assert note.created_at == datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


# ---- tag_service ----

def test_get_or_create_tags_is_case_insensitive_per_user(app):
    user = _user('a@example.com')
    first = tag_service.get_or_create_tags(user.id, ['AI'])
    db.session.commit()
    second = tag_service.get_or_create_tags(user.id, ['ai'])
    db.session.commit()

    assert first[0].id == second[0].id
    assert Tag.query.filter_by(user_id=user.id).count() == 1


def test_get_or_create_tags_dedupes_within_one_call(app):
    user = _user('a@example.com')
    tags = tag_service.get_or_create_tags(user.id, ['AI', 'ai', ' AI '])
    db.session.commit()

    assert len(tags) == 1


def test_get_or_create_tags_keeps_tags_isolated_per_user(app):
    a = _user('a@example.com')
    b = _user('b@example.com')
    tag_a = tag_service.get_or_create_tags(a.id, ['shared'])[0]
    db.session.commit()
    tag_b = tag_service.get_or_create_tags(b.id, ['shared'])[0]
    db.session.commit()

    assert tag_a.id != tag_b.id


def test_prune_orphan_tags_only_removes_that_users_unused_tags(app):
    a = _user('a@example.com')
    b = _user('b@example.com')
    note = Note(user_id=a.id, title='T', content='C')
    note.tags = tag_service.get_or_create_tags(a.id, ['used'])
    db.session.add(note)
    tag_service.get_or_create_tags(a.id, ['orphan'])
    tag_service.get_or_create_tags(b.id, ['orphan'])
    db.session.commit()

    tag_service.prune_orphan_tags(a.id)
    db.session.commit()

    remaining = {t.user_id: t.name for t in Tag.query.all()}
    assert (a.id, 'used') in remaining.items()
    assert (a.id, 'orphan') not in remaining.items()
    assert (b.id, 'orphan') in remaining.items()


# ---- category_service ----

def test_note_form_choices_has_no_artificial_intelligence_value_duplicate():
    # Regression: 'AI' is the only stored value; 'Artificial Intelligence'
    # is only ever the display label, never a second value in the same list.
    values = [value for value, _label in category_service.note_form_choices()]
    assert values.count('AI') == 1
    assert 'Artificial Intelligence' not in values


def test_category_color_known_and_unknown_categories():
    assert category_service.category_color('AI') == {'background': '#a99bea', 'border': '#5c5580'}
    assert category_service.category_color('Nonexistent') == category_service.DEFAULT_COLOR
    assert category_service.category_color(None) == category_service.DEFAULT_COLOR


def test_category_badge_class_known_and_unknown_categories():
    assert category_service.category_badge_class('AI') == 'badge-category-ai'
    assert category_service.category_badge_class('Nonexistent') == 'badge-category-none'


def test_garden_category_metadata_matches_categories_order():
    metadata = category_service.garden_category_metadata()
    assert [m['value'] for m in metadata] == [c['value'] for c in category_service.CATEGORIES]
    assert all({'value', 'label', 'short_label', 'slug'} <= m.keys() for m in metadata)
