import json
import os
import subprocess
import sys

import pytest

from app import create_app, db
from app.models import User
from config import Config

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _config_values(env, names):
    """Import config.py in a clean child process with exactly `env` set and
    .env loading disabled, and return the requested Config attributes."""
    code = (
        'import json, sys, types\n'
        "sys.modules['dotenv'] = types.SimpleNamespace(load_dotenv=lambda *a, **k: None)\n"
        'from config import Config\n'
        f'print(json.dumps({{n: getattr(Config, n) for n in {names!r}}}))\n'
    )
    child_env = {k: v for k, v in os.environ.items()
                 if k not in {'FLASK_DEBUG', 'SECRET_KEY', 'UPLOAD_MAX_SIZE_MB'}}
    child_env.update(env)
    proc = subprocess.run([sys.executable, '-B', '-c', code], env=child_env, cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _make_app(**overrides):
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    }
    config.update(overrides)
    return create_app(config)


@pytest.fixture
def app():
    app = _make_app()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    user = User(name='Test User', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return app.test_client()


def _login(client, next_param=None):
    query = {} if next_param is None else {'next': next_param}
    return client.post('/auth/login', query_string=query, data={
        'email': 'test@example.com', 'password': 'password123',
    })


# ---- S3: login `next` must never leave the site ----

@pytest.mark.parametrize('target', [
    'https://evil.example',
    'http://evil.example/notes/',
    '//evil.example',
    '///evil.example',
    '/\\evil.example',
    '\\\\evil.example',
    '\\/evil.example',
    '/\t/evil.example',
    'javascript:alert(1)',
    'http:/evil.example',
    'notes/',
])
def test_login_ignores_unsafe_next(client, target):
    response = _login(client, target)
    assert response.status_code == 302
    assert response.headers['Location'] == '/dashboard'


def test_login_follows_safe_relative_next(client):
    response = _login(client, '/notes/?page=2')
    assert response.headers['Location'] == '/notes/?page=2'


def test_login_required_round_trip_returns_to_original_page(client):
    redirect_to_login = client.get('/notes/')
    login_url = redirect_to_login.headers['Location']
    assert '/auth/login' in login_url

    response = client.post(login_url, data={
        'email': 'test@example.com', 'password': 'password123',
    })
    assert response.headers['Location'] == '/notes/'


# ---- S4: effective debug / secret-key configuration ----

def test_debug_is_off_when_flask_debug_unset():
    assert _config_values({}, ['FLASK_DEBUG']) == {'FLASK_DEBUG': False}


@pytest.mark.parametrize('value, expected', [
    ('', False), ('0', False), ('false', False), ('garbage', False),
    ('1', True), ('true', True), ('yes', True),
])
def test_flask_debug_env_parsing(value, expected):
    assert _config_values({'FLASK_DEBUG': value}, ['FLASK_DEBUG'])['FLASK_DEBUG'] is expected


@pytest.mark.parametrize('key', ['', 'dev-secret-key', 'dev-secret-key-change-in-production'])
def test_production_refuses_insecure_secret_key(key, monkeypatch):
    monkeypatch.setattr(Config, 'SECRET_KEY', 'a-real-key-from-the-environment')
    with pytest.raises(RuntimeError) as excinfo:
        _make_app(FLASK_DEBUG=False, SECRET_KEY=key)
    assert 'a-real-key-from-the-environment' not in str(excinfo.value)


def test_production_accepts_real_secret_key_override(monkeypatch):
    monkeypatch.setattr(Config, 'SECRET_KEY', 'dev-secret-key')
    monkeypatch.setattr(Config, 'FLASK_DEBUG', False)
    app = _make_app(FLASK_DEBUG=False, SECRET_KEY='a-long-random-production-key')
    assert app.config['SECRET_KEY'] == 'a-long-random-production-key'


def test_debug_with_blank_key_falls_back_to_working_dev_key():
    app = _make_app(FLASK_DEBUG=True, SECRET_KEY='')
    with app.app_context():
        db.create_all()
    assert app.config['SECRET_KEY']
    assert app.test_client().get('/auth/login').status_code == 200


def _env_example():
    with open(os.path.join(REPO_ROOT, '.env.example'), encoding='utf-8') as f:
        return dict(
            line.split('=', 1) for line in f.read().splitlines()
            if line and not line.lstrip().startswith('#') and '=' in line
        )


def test_env_example_ships_no_usable_secret_and_debug_off():
    example = _env_example()
    assert example['SECRET_KEY'].strip() == ''
    assert example['FLASK_DEBUG'].strip() == '0'


# ---- S7: logout is POST + CSRF; cookies are hardened outside debug ----

def _csrf_app():
    app = _make_app(WTF_CSRF_ENABLED=True)
    with app.app_context():
        db.create_all()
        user = User(name='Test User', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    return app


def _csrf_token(html):
    import re
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return match.group(1) if match else None


def _csrf_login(client):
    token = _csrf_token(client.get('/auth/login').data.decode())
    response = client.post('/auth/login', data={
        'email': 'test@example.com', 'password': 'password123', 'csrf_token': token,
    })
    assert response.headers['Location'] == '/dashboard'


def test_logout_rejects_get():
    client = _csrf_app().test_client()
    _csrf_login(client)

    assert client.get('/auth/logout').status_code == 405
    assert client.get('/dashboard').status_code == 200


def test_logout_post_without_csrf_token_is_rejected():
    client = _csrf_app().test_client()
    _csrf_login(client)

    assert client.post('/auth/logout').status_code == 400
    assert client.get('/dashboard').status_code == 200


def test_navbar_logout_form_logs_out_with_its_csrf_token():
    import re
    client = _csrf_app().test_client()
    _csrf_login(client)

    page = client.get('/dashboard').data.decode()
    form = re.search(r'<form[^>]*action="/auth/logout"[^>]*>.*?</form>', page, re.S)
    assert form, 'navbar has no logout form'
    assert re.search(r'method="post"', form.group(0), re.I)

    response = client.post('/auth/logout', data={'csrf_token': _csrf_token(form.group(0))})
    assert response.status_code == 302
    assert client.get('/dashboard').status_code == 302


_COOKIE_SCRIPT = r'''
import json, sys, types
sys.modules['dotenv'] = types.SimpleNamespace(load_dotenv=lambda *a, **k: None)
from app import create_app, db
from app.models import User
app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'WTF_CSRF_ENABLED': False})
with app.app_context():
    db.create_all()
    user = User(name='Cookie', email='cookie@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    response = app.test_client().post('/auth/login', data={
        'email': 'cookie@example.com', 'password': 'password123', 'remember': 'y'})
print(json.dumps(response.headers.getlist('Set-Cookie')))
'''


def _login_cookies(env):
    child_env = {k: v for k, v in os.environ.items() if k not in {'FLASK_DEBUG', 'SECRET_KEY'}}
    child_env.update(env)
    proc = subprocess.run([sys.executable, '-B', '-c', _COOKIE_SCRIPT], env=child_env,
                          cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    cookies = json.loads(proc.stdout.strip().splitlines()[-1])
    return {c.split('=', 1)[0]: c for c in cookies}


def test_production_login_cookies_are_secure_httponly_samesite():
    cookies = _login_cookies({'SECRET_KEY': 'a-long-random-production-key'})
    for name in ('session', 'remember_token'):
        assert name in cookies
        header = cookies[name]
        assert '; Secure' in header, header
        assert '; HttpOnly' in header, header
        assert 'SameSite=Lax' in header, header


def test_debug_login_cookies_are_not_marked_secure():
    cookies = _login_cookies({'FLASK_DEBUG': '1'})
    assert '; Secure' not in cookies['session']
    assert '; Secure' not in cookies['remember_token']


# ---- S9: one configured upload limit, friendly 413 ----

@pytest.fixture
def small_limit_client(monkeypatch):
    monkeypatch.setattr('app.notes.routes.queue_embedding_generation', lambda *a, **k: None)
    monkeypatch.setattr('app.services.background_indexing.queue_embedding_generation', lambda *a, **k: None)
    app = _make_app(UPLOAD_MAX_SIZE_MB=1)
    with app.app_context():
        db.create_all()
        user = User(name='Test User', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        client = app.test_client()
        _login(client)
        yield client
        db.session.remove()
        db.drop_all()


def _upload(client, size, **kwargs):
    import io
    body = (b'Knowledge garden sentence. ' * (size // 27 + 1))[:size]
    return client.post('/notes/import', data={'file': (io.BytesIO(body), 'big.txt')},
                       content_type='multipart/form-data', **kwargs)


def test_upload_over_configured_limit_redirects_with_message(small_limit_client):
    response = _upload(small_limit_client, 1536 * 1024)
    assert response.status_code == 302
    assert response.headers['Location'] == '/notes/create'

    page = small_limit_client.get('/notes/create').data.decode()
    assert 'File too large. Maximum size: 1 MB' in page
    from app.models import Note
    assert Note.query.count() == 0


def test_upload_over_limit_json_client_gets_json_413(small_limit_client):
    response = _upload(small_limit_client, 1536 * 1024, headers={'Accept': 'application/json'})
    assert response.status_code == 413
    assert response.get_json()['error'] == 'File too large. Maximum size: 1 MB.'


def test_upload_under_configured_limit_still_imports(small_limit_client):
    response = _upload(small_limit_client, 8 * 1024)
    assert response.status_code == 302
    from app.models import Note
    assert Note.query.filter_by(source_filename='big.txt').count() > 0


def test_create_page_shows_configured_upload_limit(small_limit_client):
    page = small_limit_client.get('/notes/create').data.decode()
    assert 'Max file size: 1 MB' in page


# ---- NFR: generic user-facing errors, detailed server-side logs ----

SECRET_DETAIL = 'SECRET-INTERNAL-DETAIL /srv/private/thought_garden.db'


def _boom(*args, **kwargs):
    raise RuntimeError(SECRET_DETAIL)


@pytest.fixture
def logged_in(app, client, monkeypatch):
    monkeypatch.setattr('app.notes.routes.queue_embedding_generation', lambda *a, **k: None)
    _login(client)
    return client


def _note_id(client):
    from app.models import Note
    client.post('/notes/create', data={'title': 'Existing', 'content': 'Body text.'})
    return Note.query.filter_by(title='Existing').one().id


def _assert_generic_failure(client, response, caplog, page_url):
    request_id = response.headers['X-Request-ID']
    page = client.get(page_url, follow_redirects=True).data.decode()
    assert SECRET_DETAIL not in page
    assert f'Reference: {request_id}' in page
    logged = [r for r in caplog.records if SECRET_DETAIL in r.getMessage() or
              (r.exc_info and SECRET_DETAIL in str(r.exc_info[1]))]
    assert logged, 'exception details were not logged'
    assert all(getattr(r, 'request_id', None) == request_id for r in logged)


def test_create_analysis_failure_is_generic_to_user(logged_in, caplog, monkeypatch):
    monkeypatch.setattr('app.notes.routes.update_relationships_for_note', _boom)
    response = logged_in.post('/notes/create', data={'title': 'New', 'content': 'Body.'})
    assert response.status_code == 302
    _assert_generic_failure(logged_in, response, caplog, response.headers['Location'])


def test_edit_analysis_failure_is_generic_to_user(logged_in, caplog, monkeypatch):
    note_id = _note_id(logged_in)
    monkeypatch.setattr('app.notes.routes.update_relationships_for_note', _boom)
    response = logged_in.post(f'/notes/{note_id}/edit', data={'title': 'Changed', 'content': 'Body.'})
    assert response.status_code == 302
    _assert_generic_failure(logged_in, response, caplog, response.headers['Location'])


def test_unarchive_analysis_failure_is_generic_to_user(logged_in, caplog, monkeypatch):
    note_id = _note_id(logged_in)
    logged_in.post(f'/notes/{note_id}/archive')
    monkeypatch.setattr('app.notes.routes.update_relationships_for_note', _boom)
    response = logged_in.post(f'/notes/{note_id}/archive')
    assert response.status_code == 302
    _assert_generic_failure(logged_in, response, caplog, response.headers['Location'])


def test_import_failure_is_generic_to_user(logged_in, caplog, monkeypatch):
    import io
    monkeypatch.setattr('app.services.document_service.create_notes_from_document', _boom)
    response = logged_in.post('/notes/import', data={'file': (io.BytesIO(b'Some text.'), 'a.txt')},
                              content_type='multipart/form-data')
    assert response.status_code == 302
    _assert_generic_failure(logged_in, response, caplog, response.headers['Location'])
