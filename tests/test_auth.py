import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.forms import ProfileForm, RegisterForm
from app.models import User


@pytest.fixture
def app():
    app = create_app({
        'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False, 'SECRET_KEY': 'test-secret-key',
        'LOGIN_MAX_FAILED_ATTEMPTS': 3, 'LOGIN_LOCKOUT_SECONDS': 600,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _add_user(email='test@example.com', password='password123', name='Test User'):
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def _register(client, email, name='New User'):
    return client.post('/auth/register', data={
        'name': name, 'email': email,
        'password': 'password123', 'confirm_password': 'password123',
    })


def _login(client, email='test@example.com', password='password123', ip='10.0.0.1'):
    return client.post('/auth/login', data={'email': email, 'password': password},
                       environ_overrides={'REMOTE_ADDR': ip})


# ---- C10: case-insensitive, normalized, DB-enforced email uniqueness ----

def test_model_normalizes_email():
    assert User(name='X', email='  Mixed@Example.COM ').email == 'mixed@example.com'


def test_register_stores_lowercase_email(client):
    _register(client, 'New.User@Example.COM')
    assert User.query.one().email == 'new.user@example.com'


def test_login_is_case_insensitive(client):
    _add_user()
    response = _login(client, email='  TEST@Example.com ')
    assert response.headers['Location'] == '/dashboard'


def test_register_rejects_email_differing_only_by_case(client):
    _add_user()
    response = _register(client, 'TEST@EXAMPLE.COM')
    assert b'Email already registered' in response.data
    assert User.query.count() == 1


def test_register_race_is_caught_by_database_constraint(client, monkeypatch):
    # Simulate two concurrent registrations: the form's pre-check misses the
    # other request's row, so only the database constraint can stop it.
    monkeypatch.setattr(RegisterForm, 'validate_email', lambda self, field: None)
    _add_user()
    response = _register(client, 'Test@Example.com')
    assert response.status_code == 200
    assert b'Email already registered' in response.data
    assert User.query.count() == 1


def test_database_rejects_case_duplicate_emails(app):
    _add_user()
    with pytest.raises(IntegrityError):
        db.session.execute(text(
            "INSERT INTO user (name, email, password_hash) VALUES ('Y', 'TEST@example.com', 'x')"))
        db.session.commit()
    db.session.rollback()


def test_profile_rejects_other_users_email_in_different_case(client):
    _add_user()
    _add_user(email='other@example.com', name='Other')
    _login(client)
    response = client.post('/auth/profile', data={
        'name': 'Test User', 'email': 'OTHER@example.com', 'current_password': 'password123'})
    assert b'Email already in use' in response.data
    assert User.query.filter_by(name='Test User').one().email == 'test@example.com'


def test_profile_race_is_caught_by_database_constraint(client, monkeypatch):
    monkeypatch.setattr(ProfileForm, 'validate_email', lambda self, field: None)
    _add_user()
    _add_user(email='other@example.com', name='Other')
    _login(client)
    response = client.post('/auth/profile', data={
        'name': 'Test User', 'email': 'other@example.com', 'current_password': 'password123'})
    assert response.status_code == 200
    assert b'Email already in use' in response.data
    assert User.query.filter_by(name='Test User').one().email == 'test@example.com'


# ---- S6: changing email requires the current password ----

@pytest.mark.parametrize('password, message', [
    ('', b'Enter your current password to change your email'),
    ('wrong-password', b'Current password is incorrect'),
])
def test_email_change_requires_correct_current_password(client, password, message):
    _add_user()
    _login(client)
    response = client.post('/auth/profile', data={
        'name': 'Test User', 'email': 'new@example.com', 'current_password': password})
    assert message in response.data
    assert User.query.one().email == 'test@example.com'


def test_email_change_with_correct_password_succeeds(client):
    _add_user()
    _login(client)
    response = client.post('/auth/profile', data={
        'name': 'Test User', 'email': 'New@Example.com', 'current_password': 'password123'})
    assert response.status_code == 302
    assert User.query.one().email == 'new@example.com'


def test_name_change_does_not_require_password(client):
    _add_user()
    _login(client)
    response = client.post('/auth/profile', data={'name': 'Renamed', 'email': 'test@example.com'})
    assert response.status_code == 302
    assert User.query.one().name == 'Renamed'


# ---- S5: failed-login rate limit per client IP ----

def _exhaust(client, ip='10.0.0.1'):
    for _ in range(3):
        assert _login(client, password='wrong', ip=ip).status_code == 200


def test_login_blocked_after_too_many_failures(client):
    _add_user()
    _exhaust(client)

    response = _login(client, ip='10.0.0.1')

    assert response.status_code == 429
    assert b'Too many failed login attempts' in response.data
    assert client.get('/dashboard').status_code == 302


def test_login_limit_is_per_client_ip(client):
    _add_user()
    _exhaust(client, ip='10.0.0.1')

    assert _login(client, ip='10.0.0.2').headers['Location'] == '/dashboard'


def test_login_allowed_again_after_lockout_window(app, client):
    _add_user()
    now = [1000.0]
    _login(client, password='wrong')
    limiter = app.extensions['login_limiter']
    limiter.clock = lambda: now[0]
    limiter.reset()
    _exhaust(client)
    assert _login(client).status_code == 429

    now[0] += 601
    assert _login(client).headers['Location'] == '/dashboard'
