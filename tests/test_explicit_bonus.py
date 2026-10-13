"""Shared tags and category add to embedding similarity (similarity_service
explicit bonus): the user's own organisation connects notes whose wording
differs, while broad tags carry little weight."""

import math

import numpy as np
import pytest

from app import create_app, db
from app.models import Note, NoteEmbedding, Relationship, Tag, User
from app.services import similarity_service
from app.services.similarity_service import rebuild_user_graph, same_category, tag_weights


@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                      'WTF_CSRF_ENABLED': False, 'SECRET_KEY': 'test-secret-key'})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def _garden(notes_spec):
    """notes_spec: [(name, angle_degrees, category, [tags])] -> {name: Note}.
    Unit 2-D embeddings make cosine = cos(angle difference)."""
    user = User(name='G', email='bonus@test.com')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    tags = {}
    out = {}
    for name, angle, category, tag_names in notes_spec:
        note = Note(user_id=user.id, title=name, content=f'{name} text.', category=category)
        db.session.add(note)
        db.session.flush()
        for t in tag_names:
            if t not in tags:
                tags[t] = Tag(user_id=user.id, name=t)
        note.tags = [tags[t] for t in tag_names]
        rad = math.radians(angle)
        db.session.add(NoteEmbedding(note_id=note.id,
                                     embedding=np.array([math.cos(rad), math.sin(rad)], dtype=np.float32).tobytes()))
        out[name] = note
    db.session.commit()
    rebuild_user_graph(user.id)
    return out


def _linked(a, b):
    return Relationship.query.filter(
        ((Relationship.source_note_id == a.id) & (Relationship.target_note_id == b.id))
        | ((Relationship.source_note_id == b.id) & (Relationship.target_note_id == a.id))
    ).first()


def test_rare_shared_tag_connects_notes_the_model_scores_low(app):
    # 78 degrees apart: cosine 0.21, far below the 0.45 threshold on its own.
    notes = _garden([
        ('joins', 0, 'Study', ['Databases']),
        ('normalisation', 78, 'Study', ['Databases']),
        ('poem', 160, 'Writing', ['poetry']),
        ('story', 200, 'Writing', ['story idea']),
    ])
    rel = _linked(notes['joins'], notes['normalisation'])
    assert rel is not None
    assert rel.method == 'embedding'
    # one fully-weighted shared tag (+0.20) and the same category (+0.05)
    assert rel.similarity_score == pytest.approx(math.cos(math.radians(78)) + 0.20 + 0.05, abs=1e-3)


def test_broad_tag_on_most_notes_does_not_wire_the_garden_together(app):
    # Everything shares "exam prep"; it is on 5 of 6 notes, so it weighs ~0.1.
    spec = [(f'n{i}', i * 70, None, ['exam prep']) for i in range(5)] + [('other', 300, None, ['misc'])]
    notes = _garden(spec)
    # 70 degrees apart: cosine 0.34 - not enough even with the broad tag.
    assert _linked(notes['n0'], notes['n1']) is None


def test_without_tags_or_category_the_threshold_is_unchanged(app):
    notes = _garden([
        ('a', 0, None, []),
        ('b', 60, None, []),   # cosine 0.50 -> linked
        ('c', 65, None, []),   # cosine 0.42 to a -> not linked
    ])
    assert _linked(notes['a'], notes['b']) is not None
    assert _linked(notes['a'], notes['c']) is None


def test_tag_weights_favour_rare_tags():
    class T:
        def __init__(self, name):
            self.name = name

    class N:
        def __init__(self, *tags):
            self.tags = [T(t) for t in tags]

    weights = tag_weights([N('Databases', 'exam prep'), N('databases', 'exam prep'), N('exam prep'), N('exam prep'),
                           N('exam prep'), N('poetry'), N('poetry'), N('x')])
    assert weights['databases'] == pytest.approx(1.0)
    assert weights['exam prep'] < 0.5
    assert weights['databases'] == weights['poetry']


def test_same_category_matches_text_and_shared_palette_but_not_blank():
    assert same_category('Writing', 'writing')
    assert same_category('Cybersecurity', 'Study')   # retired preset reads as Study
    assert not same_category('Travel', 'Hiking')     # two unbranded customs
    assert not same_category(None, None)
    assert not same_category('Writing', None)


def test_bonus_never_pushes_a_score_above_one(app):
    notes = _garden([
        ('a', 0, 'Writing', ['poetry', 'rain']),
        ('b', 1, 'Writing', ['poetry', 'rain']),
        ('c', 180, None, []),
    ])
    assert _linked(notes['a'], notes['b']).similarity_score <= 1.0
    assert similarity_service.MAX_EXPLICIT_BONUS == pytest.approx(0.30)
