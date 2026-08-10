import pytest
from app import create_app, db
from app.models import User, Note, Tag, Relationship


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
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200


def test_create_note(auth_client):
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


def test_edit_note(auth_client):
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


def test_delete_note(auth_client):
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


def test_archive_note(auth_client):
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


def test_pin_note(auth_client):
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


def test_note_ownership(client):
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
    
    client.get('/auth/logout', follow_redirects=True)
    
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


def test_no_self_relationship(client):
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