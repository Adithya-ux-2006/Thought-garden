import math
import numpy as np
import pytest
from app import create_app, db
from app.models import User, Note, Tag, Relationship, NoteEmbedding
from app.services.similarity_service import rebuild_user_graph


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    return client


def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Thought Garden' in response.data


def test_register(client):
    response = client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_register_duplicate_email(client):
    client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    # register() auto-logs-in the new user on success, and redirects any
    # already-authenticated request straight to the dashboard before the
    # duplicate-email check ever runs. Without logging out first, this
    # second POST never exercises that check - it just bounces to
    # /dashboard, which is what made this test look broken.
    client.post('/auth/logout', follow_redirects=True)

    response = client.post('/auth/register', data={
        'name': 'Test User 2',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert b'Email already registered' in response.data


def test_login(client):
    client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back' in response.data


def test_login_invalid_credentials(client):
    response = client.post('/auth/login', data={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid email or password' in response.data


def test_logout(auth_client):
    response = auth_client.post('/auth/logout', follow_redirects=True)
    assert response.status_code == 200


def test_create_note(auth_client, app):
    response = auth_client.post('/notes/create', data={
        'title': 'Test Note',
        'content': 'This is a test note.',
        'category': 'AI',
        'tags': 'test, note',
        'is_pinned': False
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        note = Note.query.filter_by(title='Test Note').first()
        assert note is not None
        assert note.content == 'This is a test note.'
        assert note.category == 'AI'


def test_edit_note(auth_client, app):
    auth_client.post('/notes/create', data={
        'title': 'Test Note',
        'content': 'This is a test note.',
        'category': 'AI',
        'tags': 'test',
        'is_pinned': False
    }, follow_redirects=True)
    
    with app.app_context():
        note = Note.query.filter_by(title='Test Note').first()
        note_id = note.id
    
    response = auth_client.post(f'/notes/{note_id}/edit', data={
        'title': 'Updated Note',
        'content': 'This is an updated note.',
        'category': 'Research',
        'tags': 'test, updated',
        'is_pinned': True
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        note = Note.query.get(note_id)
        assert note.title == 'Updated Note'
        assert note.content == 'This is an updated note.'
        assert note.category == 'Research'
        assert note.is_pinned == True


def test_delete_note(auth_client, app):
    auth_client.post('/notes/create', data={
        'title': 'Test Note',
        'content': 'This is a test note.',
        'category': 'AI',
        'tags': 'test',
        'is_pinned': False
    }, follow_redirects=True)
    
    with app.app_context():
        note = Note.query.filter_by(title='Test Note').first()
        note_id = note.id
    
    response = auth_client.post(f'/notes/{note_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        note = Note.query.get(note_id)
        assert note is None


def test_two_users_can_independently_use_the_same_tag_name(client, app):
    # End-to-end regression for the tag cross-user leak: creating a note
    # tagged 'ai' as one user must not reuse or collide with another
    # user's identically-named tag.
    client.post('/auth/register', data={
        'name': 'User One', 'email': 'one@example.com',
        'password': 'password123', 'confirm_password': 'password123',
    }, follow_redirects=True)
    client.post('/notes/create', data={
        'title': 'Note One', 'content': 'First.', 'tags': 'shared', 'is_pinned': False,
    }, follow_redirects=True)
    client.post('/auth/logout', follow_redirects=True)

    client.post('/auth/register', data={
        'name': 'User Two', 'email': 'two@example.com',
        'password': 'password123', 'confirm_password': 'password123',
    }, follow_redirects=True)
    client.post('/notes/create', data={
        'title': 'Note Two', 'content': 'Second.', 'tags': 'shared', 'is_pinned': False,
    }, follow_redirects=True)

    with app.app_context():
        tags = Tag.query.filter_by(name='shared').all()
        assert len(tags) == 2
        assert {t.user_id for t in tags} == {
            User.query.filter_by(email='one@example.com').one().id,
            User.query.filter_by(email='two@example.com').one().id,
        }


def test_removing_a_notes_only_tag_prunes_the_orphaned_tag(auth_client, app):
    auth_client.post('/notes/create', data={
        'title': 'Tagged Note', 'content': 'Content.', 'tags': 'onlyhere', 'is_pinned': False,
    }, follow_redirects=True)

    with app.app_context():
        note_id = Note.query.filter_by(title='Tagged Note').one().id
        assert Tag.query.filter_by(name='onlyhere').count() == 1

    auth_client.post(f'/notes/{note_id}/edit', data={
        'title': 'Tagged Note', 'content': 'Content.', 'tags': '', 'is_pinned': False,
    }, follow_redirects=True)

    with app.app_context():
        assert Tag.query.filter_by(name='onlyhere').count() == 0


def test_archive_note(auth_client, app):
    auth_client.post('/notes/create', data={
        'title': 'Test Note',
        'content': 'This is a test note.',
        'category': 'AI',
        'tags': 'test',
        'is_pinned': False
    }, follow_redirects=True)
    
    with app.app_context():
        note = Note.query.filter_by(title='Test Note').first()
        note_id = note.id
    
    response = auth_client.post(f'/notes/{note_id}/archive', follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        note = Note.query.get(note_id)
        assert note.is_archived == True


def test_pin_note(auth_client, app):
    auth_client.post('/notes/create', data={
        'title': 'Test Note',
        'content': 'This is a test note.',
        'category': 'AI',
        'tags': 'test',
        'is_pinned': False
    }, follow_redirects=True)
    
    with app.app_context():
        note = Note.query.filter_by(title='Test Note').first()
        note_id = note.id
    
    response = auth_client.post(f'/notes/{note_id}/pin', follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        note = Note.query.get(note_id)
        assert note.is_pinned == True


def test_search(auth_client):
    auth_client.post('/notes/create', data={
        'title': 'Machine Learning',
        'content': 'Machine learning is a subset of AI.',
        'category': 'AI',
        'tags': 'AI, ML',
        'is_pinned': False
    }, follow_redirects=True)
    
    response = auth_client.get('/search/?q=machine', follow_redirects=True)
    assert response.status_code == 200
    assert b'Machine Learning' in response.data


def test_note_ownership(client, app):
    client.post('/auth/register', data={
        'name': 'User 1',
        'email': 'user1@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    client.post('/notes/create', data={
        'title': 'User 1 Note',
        'content': 'This is user 1 note.',
        'category': 'AI',
        'tags': 'test',
        'is_pinned': False
    }, follow_redirects=True)
    
    client.post('/auth/logout', follow_redirects=True)
    
    client.post('/auth/register', data={
        'name': 'User 2',
        'email': 'user2@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    with app.app_context():
        note = Note.query.filter_by(title='User 1 Note').first()
        note_id = note.id
    
    response = client.get(f'/notes/{note_id}', follow_redirects=True)
    assert response.status_code == 404


def test_archiving_note_removes_dangling_garden_edges(client, app):
    with app.app_context():
        user = User(name='Test', email='archive-garden@test.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        note1 = Note(user_id=user.id, title='Note 1', content='Content 1')
        note2 = Note(user_id=user.id, title='Note 2', content='Content 2')
        note3 = Note(user_id=user.id, title='Note 3', content='Content 3')
        note4 = Note(user_id=user.id, title='Note 4', content='Content 4')
        db.session.add_all([note1, note2, note3, note4])
        db.session.commit()

        # note1 connected to all three others - archiving it should drop
        # exactly these relationships, leaving no edge that references it.
        db.session.add_all([
            Relationship(source_note_id=note1.id, target_note_id=note2.id, similarity_score=0.9),
            Relationship(source_note_id=note1.id, target_note_id=note3.id, similarity_score=0.8),
            Relationship(source_note_id=note4.id, target_note_id=note1.id, similarity_score=0.7),
            Relationship(source_note_id=note2.id, target_note_id=note3.id, similarity_score=0.6),
        ])
        db.session.commit()
        note1_id = note1.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.post(f'/notes/{note1_id}/archive', follow_redirects=True)
    assert response.status_code == 200

    response = client.get('/garden/data')
    assert response.status_code == 200
    data = response.get_json()

    visible_ids = {n['id'] for n in data['nodes']}
    assert note1_id not in visible_ids
    for edge in data['edges']:
        assert edge['from'] != note1_id
        assert edge['to'] != note1_id
        assert edge['from'] in visible_ids
        assert edge['to'] in visible_ids


def _unit_vector(angle_degrees):
    rad = math.radians(angle_degrees)
    return np.array([math.cos(rad), math.sin(rad)], dtype=np.float32)


def _set_embedding(note_id, angle_degrees):
    row = db.session.get(NoteEmbedding, note_id)
    blob = _unit_vector(angle_degrees).tobytes()
    if row is None:
        db.session.add(NoteEmbedding(note_id=note_id, embedding=blob))
    else:
        row.embedding = blob
    db.session.commit()


def test_editing_note_does_not_destroy_other_notes_connections(client, app):
    with app.app_context():
        user = User(name='Test', email='edit-connections@test.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        # A (the note about to be edited) plus B..F (a tight cluster) and
        # G..I (a second tight cluster). Angles are chosen so the cosine
        # threshold (0.45, ~63 degrees) cleanly separates "qualifies" from
        # "doesn't", with no ties - see similarity_service fix commit for
        # the full geometry writeup.
        names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
        notes = {}
        for name in names:
            note = Note(user_id=user.id, title=f'Note {name}', content=f'Content for note {name}.')
            db.session.add(note)
            notes[name] = note
        db.session.commit()

        # A starts inside the G/H/I cluster (91 degrees) - before the
        # edit, A's only qualifying matches are G, H, I.
        _set_embedding(notes['A'].id, 91)
        for name, angle in [('B', 0), ('C', 2), ('D', 4), ('E', 6), ('F', 8)]:
            _set_embedding(notes[name].id, angle)
        for name, angle in [('G', 90), ('H', 92), ('I', 94)]:
            _set_embedding(notes[name].id, angle)

        # Build the initial graph exactly like the real app would: a full
        # rebuild from the current embeddings.
        rebuild_user_graph(user.id)

        def connections_of(name):
            rels = Relationship.query.filter(
                (Relationship.source_note_id == notes[name].id) |
                (Relationship.target_note_id == notes[name].id)
            ).all()
            return {
                (rel.target_note_id if rel.source_note_id == notes[name].id else rel.source_note_id)
                for rel in rels
            }

        before = {name: connections_of(name) for name in names}

        # Sanity check the setup actually reproduces the reported bug
        # scenario before trusting the "nothing lost" assertion below.
        assert notes['G'].id in before['A']
        assert notes['H'].id in before['A']
        assert notes['I'].id in before['A']

        # The edit: move A out of the G/H/I cluster into the B..F cluster
        # (44 degrees - still within threshold of G/H/I at ~0.64-0.69
        # similarity, just no longer competitive against B..F at
        # ~0.72-0.80). A's own top-5 will now pick B..F, crowding out
        # G/H/I even though G/H/I still qualify and still want A.
        _set_embedding(notes['A'].id, 44)
        rebuild_user_graph(user.id)

        after = {name: connections_of(name) for name in names}

        # The actual bug fix: G, H and I never touched anything, so their
        # connection to A must survive even though A itself dropped them
        # from its own top pick.
        assert notes['A'].id in after['G']
        assert notes['A'].id in after['H']
        assert notes['A'].id in after['I']

        # General property: no note other than the one edited may have
        # lost a connection it had before, though it may gain new ones.
        for name in names:
            if name == 'A':
                continue
            lost = before[name] - after[name]
            assert not lost, f'Note {name} lost connections {lost} it never asked to lose'


def test_no_self_relationship(client, app):
    with app.app_context():
        user = User(name='Test', email='test@test.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        note1 = Note(user_id=user.id, title='Note 1', content='Content 1')
        note2 = Note(user_id=user.id, title='Note 2', content='Content 2')
        db.session.add_all([note1, note2])
        db.session.commit()
        
        rel = Relationship(source_note_id=note1.id, target_note_id=note1.id, similarity_score=0.9)
        db.session.add(rel)
        
        with pytest.raises(Exception):
            db.session.commit()