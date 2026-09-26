"""Server-side coverage for Phase 5 (UX + accessibility + CSP)."""
import re
from html.parser import HTMLParser

import pytest
from flask import g

from app import create_app, db
from app.models import Note, Relationship, Tag, User


def _make_app(**overrides):
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    }
    config.update(overrides)
    return create_app(config)


def _app_fixture(**overrides):
    app = _make_app(**overrides)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app():
    yield from _app_fixture()


@pytest.fixture
def csrf_app():
    yield from _app_fixture(WTF_CSRF_ENABLED=True)


def _user(email='ux@example.com', name='UX User'):
    user = User(name=name, email=email)
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


def _note(user, title='Note', content='Body text', **kwargs):
    note = Note(user_id=user.id, title=title, content=content, **kwargs)
    db.session.add(note)
    db.session.commit()
    return note


def _login(client, email='ux@example.com'):
    return client.post('/auth/login', data={'email': email, 'password': 'password123'})


def _csrf_login(client, email='ux@example.com'):
    token = _csrf_from(client.get('/auth/login').get_data(as_text=True))
    return client.post('/auth/login', data={'email': email, 'password': 'password123', 'csrf_token': token})


def _csrf_from(html):
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html) or \
        re.search(r'value="([^"]+)"[^>]*name="csrf_token"', html)
    assert match, 'no csrf_token in page'
    return match.group(1)


class _Doc(HTMLParser):
    """Minimal DOM-ish collector: forms with their inputs, buttons/links with text."""

    VOID = {'input', 'img', 'br', 'hr', 'meta', 'link'}

    def __init__(self):
        super().__init__()
        self.forms = []
        self.controls = []
        self.scripts = []
        self.elements = []
        self._stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == 'form':
            self.forms.append({'attrs': attrs, 'inputs': []})
        if tag == 'input' and self.forms:
            self.forms[-1]['inputs'].append(attrs)
        if tag == 'script':
            self.scripts.append(attrs)
        if tag in ('button', 'a'):
            self.controls.append({'tag': tag, 'attrs': attrs, 'text': ''})
            self._stack.append(self.controls[-1])
        elif tag not in self.VOID:
            self._stack.append(None)

    def handle_endtag(self, tag):
        if self._stack:
            self._stack.pop()

    def handle_data(self, data):
        for item in self._stack:
            if item is not None:
                item['text'] += data


def _parse(html):
    doc = _Doc()
    doc.feed(html)
    return doc


# ---------------------------------------------------------------------------
# Unit 2: delete on note view; CSRF on every state-changing form
# ---------------------------------------------------------------------------

def test_note_view_has_a_csrf_protected_delete_form(app):
    user = _user()
    note = _note(user)
    client = app.test_client()
    _login(client)

    doc = _parse(client.get(f'/notes/{note.id}').get_data(as_text=True))
    delete_forms = [f for f in doc.forms if f['attrs'].get('action') == f'/notes/{note.id}/delete']
    assert len(delete_forms) == 1
    form = delete_forms[0]
    assert form['attrs'].get('method', '').upper() == 'POST'
    assert any(i.get('name') == 'csrf_token' for i in form['inputs'])
    assert form['attrs'].get('data-confirm'), 'delete must ask for confirmation'
    assert 'onsubmit' not in form['attrs']


def test_delete_from_view_requires_csrf_token(csrf_app):
    user = _user()
    note = _note(user)
    client = csrf_app.test_client()
    _csrf_login(client)

    assert client.post(f'/notes/{note.id}/delete').status_code == 400
    assert db.session.get(Note, note.id) is not None

    token = _csrf_from(client.get(f'/notes/{note.id}').get_data(as_text=True))
    response = client.post(f'/notes/{note.id}/delete', data={'csrf_token': token})
    assert response.status_code == 302
    db.session.expire_all()
    assert db.session.get(Note, note.id) is None


def test_delete_is_post_only_and_owner_only(app):
    owner = _user()
    note = _note(owner)
    _user(email='other@example.com', name='Other')
    client = app.test_client()
    _login(client, 'other@example.com')

    assert client.get(f'/notes/{note.id}/delete').status_code == 405
    assert client.post(f'/notes/{note.id}/delete').status_code == 404
    assert db.session.get(Note, note.id) is not None


def test_every_post_form_on_note_pages_carries_a_csrf_token(csrf_app):
    user = _user()
    note = _note(user, is_pinned=True)
    client = csrf_app.test_client()
    _csrf_login(client)

    for path in ('/notes/', f'/notes/{note.id}', f'/notes/{note.id}/edit', '/notes/create',
                 '/dashboard', '/garden/', '/search/', '/auth/profile', '/garden/list'):
        response = client.get(path)
        if response.status_code == 404 and path == '/garden/list':
            continue  # covered once the list view exists
        assert response.status_code == 200, path
        doc = _parse(response.get_data(as_text=True))
        for form in doc.forms:
            if form['attrs'].get('method', 'GET').upper() != 'POST':
                continue
            assert any(i.get('name') == 'csrf_token' for i in form['inputs']), (path, form['attrs'])


def test_list_page_pin_form_works_with_csrf_enabled(csrf_app):
    user = _user()
    note = _note(user)
    client = csrf_app.test_client()
    _csrf_login(client)

    html = client.get('/notes/').get_data(as_text=True)
    doc = _parse(html)
    pin_form = next(f for f in doc.forms if f['attrs'].get('action') == f'/notes/{note.id}/pin')
    token = next(i['value'] for i in pin_form['inputs'] if i.get('name') == 'csrf_token')
    assert client.post(f'/notes/{note.id}/pin', data={'csrf_token': token}).status_code == 302
    db.session.expire_all()
    assert db.session.get(Note, note.id).is_pinned


# ---------------------------------------------------------------------------
# Unit 3: "why connected" for related notes (reuses stored Relationship rows)
# ---------------------------------------------------------------------------

def _tagged_pair(method='keyword', score=0.5):
    user = _user()
    a = _note(user, title='Neural networks intro',
              content='Backpropagation trains neural networks with gradient descent.', category='AI')
    b = _note(user, title='Gradient descent notes',
              content='Gradient descent minimises loss; backpropagation computes gradients.', category='AI')
    a.tags = [Tag(user_id=user.id, name='Deep-Learning'), Tag(user_id=user.id, name='Solo')]
    b.tags = [a.tags[0]]
    rel = Relationship(source_note_id=a.id, target_note_id=b.id, similarity_score=score,
                       relationship_type='semantic', method=method)
    db.session.add(rel)
    db.session.commit()
    return user, a, b, rel


def test_explain_connection_reports_shared_signals(app):
    from app.services.similarity_service import explain_connection
    _, a, b, rel = _tagged_pair(method='keyword', score=0.5)

    why = explain_connection(a, b, rel)
    assert why['method'] == 'keyword'
    assert why['label'] == 'Strong match'
    assert why['shared_tags'] == ['Deep-Learning']
    assert 'backpropagation' in why['shared_keywords']
    assert 'gradient' in why['shared_keywords']
    assert why['same_category'] == 'AI'
    assert 'Deep-Learning' in why['reason'] and 'backpropagation' in why['reason']


def test_explain_connection_names_the_embedding_basis(app):
    from app.services.similarity_service import explain_connection
    user = _user()
    a = _note(user, title='Alpha', content='Completely different words here')
    b = _note(user, title='Omega', content='Nothing overlapping whatsoever')
    rel = Relationship(source_note_id=a.id, target_note_id=b.id, similarity_score=0.5,
                       relationship_type='semantic', method='embedding')
    db.session.add(rel)
    db.session.commit()

    why = explain_connection(a, b, rel)
    assert why['label'] == 'Related'
    assert why['shared_tags'] == [] and why['shared_keywords'] == [] and why['same_category'] is None
    assert why['reason'] == 'Similar overall meaning.'


def test_note_view_shows_why_each_note_is_connected(app):
    _, a, b, _ = _tagged_pair()
    client = app.test_client()
    _login(client)

    html = client.get(f'/notes/{a.id}').get_data(as_text=True)
    assert 'Gradient descent notes' in html
    assert 'Shared tags: Deep-Learning' in html
    assert 'Strong match' in html


@pytest.mark.parametrize('page', ['note', 'garden_list'])
def test_why_connected_escapes_user_content(app, page):
    user, a, b, _ = _tagged_pair()
    a.tags[0].name = '<img src=x onerror=alert(1)>'
    db.session.commit()
    client = app.test_client()
    _login(client)

    path = f'/notes/{a.id}' if page == 'note' else '/garden/list'
    html = client.get(path).get_data(as_text=True)
    assert 'Shared tags:' in html
    assert '<img src=x onerror' not in html
    assert '&lt;img src=x onerror=alert(1)&gt;' in html


def test_garden_panel_json_includes_connection_reason(app):
    _, a, b, _ = _tagged_pair()
    client = app.test_client()
    _login(client)

    data = client.get(f'/garden/note/{a.id}').get_json()
    (conn,) = data['connections']
    assert conn['id'] == b.id
    assert conn['label'] == 'Strong match'
    assert conn['method'] == 'keyword'
    assert conn['shared_tags'] == ['Deep-Learning']
    assert 'Shared tags: Deep-Learning' in conn['reason']


# ---------------------------------------------------------------------------
# Unit 4: tag suggestions on create/edit (reuses keyword_service.suggest_tags)
# ---------------------------------------------------------------------------

def test_suggest_tags_matches_existing_user_tags_and_related_note_tags():
    from app.services.keyword_service import suggest_tags

    class _N:
        def __init__(self, names):
            self.tags = [type('T', (), {'name': n})() for n in names]

    suggestions = suggest_tags(
        'Backpropagation in neural nets',
        'Neural networks learn by backpropagation. Neural layers stack.',
        current_tags=['deep-learning'],
        user_tags=['Neural-Networks', 'Cooking', 'Deep-Learning', 'Backpropagation'],
        related_notes=[_N(['Optimization', 'deep-learning'])],
    )
    assert suggestions == ['Neural-Networks', 'Backpropagation', 'Optimization']


def test_suggest_tags_is_deterministic_and_capped():
    from app.services.keyword_service import suggest_tags
    tags = ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel']
    text = ' '.join(tags)
    first = suggest_tags('', text, current_tags=[], user_tags=tags, related_notes=[])
    assert len(first) == 5
    assert all(suggest_tags('', text, current_tags=[], user_tags=tags, related_notes=[]) == first
               for _ in range(5))


def test_suggest_tags_endpoint_uses_only_the_current_users_tags(app):
    user = _user()
    _note(user, title='Tagged', content='x').tags = [Tag(user_id=user.id, name='Kubernetes')]
    other = _user(email='other@example.com', name='Other')
    _note(other, title='Theirs', content='x').tags = [Tag(user_id=other.id, name='Kubernetes-Secret')]
    db.session.commit()
    client = app.test_client()
    _login(client)

    response = client.post('/notes/api/suggest-tags',
                           json={'title': 'Deploying kubernetes', 'content': 'kubernetes pods', 'tags': ''})
    assert response.status_code == 200
    assert response.get_json() == {'suggestions': ['Kubernetes']}


def test_suggest_tags_endpoint_uses_related_notes_of_owned_note_only(app):
    user, a, b, _ = _tagged_pair()
    b.tags.append(Tag(user_id=user.id, name='Optimisation'))
    db.session.commit()
    client = app.test_client()
    _login(client)

    data = client.post('/notes/api/suggest-tags',
                       json={'title': a.title, 'content': a.content, 'tags': 'Deep-Learning',
                             'note_id': a.id}).get_json()
    assert 'Optimisation' in data['suggestions']
    assert 'Deep-Learning' not in data['suggestions']

    _user(email='other@example.com', name='Other')
    g.pop('_login_user', None)  # the fixture's app context outlives each request
    other_client = app.test_client()
    _login(other_client, 'other@example.com')
    data = other_client.post('/notes/api/suggest-tags',
                             json={'title': 'x', 'content': 'y', 'note_id': a.id}).get_json()
    assert data == {'suggestions': []}


def test_suggest_tags_endpoint_requires_login_post_and_csrf(csrf_app):
    _user()
    client = csrf_app.test_client()
    # CSRF runs before login_required, so an anonymous POST is refused either way.
    assert client.post('/notes/api/suggest-tags', json={}).status_code in (302, 400, 401)

    _csrf_login(client)
    assert client.get('/notes/api/suggest-tags').status_code == 405
    assert client.post('/notes/api/suggest-tags', json={'title': 'x'}).status_code == 400

    page = client.get('/notes/create').get_data(as_text=True)
    token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page).group(1)
    response = client.post('/notes/api/suggest-tags', json={'title': 'x', 'content': 'y'},
                           headers={'X-CSRFToken': token})
    assert response.status_code == 200


@pytest.mark.parametrize('path_kind', ['create', 'edit'])
def test_note_forms_offer_accessible_tag_suggestions(app, path_kind):
    user = _user()
    note = _note(user)
    client = app.test_client()
    _login(client)

    path = '/notes/create' if path_kind == 'create' else f'/notes/{note.id}/edit'
    doc = _parse(client.get(path).get_data(as_text=True))
    buttons = [c for c in doc.controls if c['attrs'].get('id') == 'suggestTagsButton']
    assert len(buttons) == 1
    assert buttons[0]['attrs'].get('type') == 'button'
    assert buttons[0]['attrs'].get('data-suggest-url') == '/notes/api/suggest-tags'
    region = [attrs for tag, attrs in doc.elements if attrs.get('id') == 'tagSuggestions']
    assert region and region[0].get('aria-live') == 'polite'


# ---------------------------------------------------------------------------
# Units 5-7: theme init in <head>, persistent error flashes, labelled icon buttons
# ---------------------------------------------------------------------------

def _head(html):
    return html.split('</head>', 1)[0]


def test_theme_is_initialised_by_a_blocking_head_script(app):
    html = app.test_client().get('/auth/login').get_data(as_text=True)
    head = _head(html)
    match = re.search(r'<script src="(/static/js/theme-init\.js)"></script>', head)
    assert match, 'theme-init.js must be a synchronous script in <head>'
    assert head.index('theme-init.js') < head.index('css/style.css')

    source = app.test_client().get(match.group(1)).get_data(as_text=True)
    assert "localStorage.getItem('darkMode')" in source
    assert 'data-bs-theme' in source


@pytest.mark.parametrize('category,persists', [
    ('error', True), ('danger', True), ('warning', True), ('success', False), ('info', False),
])
def test_only_non_error_flashes_auto_dismiss(app, category, persists):
    _user()
    client = app.test_client()
    _login(client)
    with client.session_transaction() as session:
        session['_flashes'] = [(category, 'Something happened')]

    doc = _parse(client.get('/dashboard').get_data(as_text=True))
    alerts = [a for t, a in doc.elements if 'alert' in a.get('class', '').split()]
    assert len(alerts) == 1
    assert ('data-autodismiss' in alerts[0]) is not persists
    close = [c for c in doc.controls if 'btn-close' in c['attrs'].get('class', '')]
    assert close and close[0]['attrs'].get('aria-label')


def _authenticated_pages(user):
    note = _note(user, title='Pinned note', content='Some text', category='AI', is_pinned=True)
    _note(user, title='Second note', content='More text', category='AI')
    return ['/dashboard', '/notes/', f'/notes/{note.id}', f'/notes/{note.id}/edit', '/notes/create',
            '/garden/', '/garden/list', f'/garden/focus/{note.id}', '/search/', '/search/?q=text',
            '/insights', '/auth/profile']


def _unlabelled_controls(html):
    doc = _parse(html)
    return [c for c in doc.controls
            if not c['text'].strip()
            and not c['attrs'].get('aria-label')
            and not c['attrs'].get('aria-labelledby')]


def test_every_icon_only_control_has_an_accessible_name(app):
    user = _user()
    pages = _authenticated_pages(user)
    client = app.test_client()
    for path in ('/', '/auth/login', '/auth/register'):
        response = client.get(path)
        assert response.status_code == 200, path
        assert _unlabelled_controls(response.get_data(as_text=True)) == [], path

    _login(client)
    for path in pages:
        response = client.get(path)
        assert response.status_code == 200, path
        assert _unlabelled_controls(response.get_data(as_text=True)) == [], path



# ---------------------------------------------------------------------------
# Unit 8: accessible list-view alternative to the graph
# ---------------------------------------------------------------------------

def test_garden_list_view_shows_notes_stages_and_connection_reasons(app):
    user, a, b, _ = _tagged_pair()
    archived = _note(user, title='Archived thing', content='x', is_archived=True)
    db.session.add(Relationship(source_note_id=a.id, target_note_id=archived.id,
                                similarity_score=0.9, relationship_type='semantic', method='keyword'))
    db.session.commit()
    client = app.test_client()
    _login(client)

    response = client.get('/garden/list')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Neural networks intro' in html and 'Gradient descent notes' in html
    assert 'Archived thing' not in html, 'archived notes and their edges stay hidden, as in the graph'
    assert 'Shared tags: Deep-Learning' in html
    assert re.search(r'(Seed|Sprout|Sapling|Tree)', html)

    doc = _parse(html)
    note_links = [c for c in doc.controls if c['attrs'].get('href') == f'/notes/{b.id}']
    assert note_links, 'each connection links to the connected note'
    assert any(t == 'h1' for t, _ in doc.elements)


def test_garden_list_view_is_user_scoped_and_needs_login(app):
    _, a, _, _ = _tagged_pair()
    client = app.test_client()
    assert client.get('/garden/list').status_code == 302

    _user(email='other@example.com', name='Other')
    _login(client, 'other@example.com')
    html = client.get('/garden/list').get_data(as_text=True)
    assert 'Neural networks intro' not in html


def test_garden_graph_page_links_to_the_list_view(app):
    _user()
    client = app.test_client()
    _login(client)
    doc = _parse(client.get('/garden/').get_data(as_text=True))
    assert any(c['attrs'].get('href') == '/garden/list' and c['text'].strip() for c in doc.controls)


# ---------------------------------------------------------------------------
# Units 9-11: vis-network scoping, no inline script/handlers/styles, CSP
# ---------------------------------------------------------------------------

VIS_SRC = '/static/vendor/vis-network/9.1.9/vis-network.min.js'
GRAPH_PAGES = {'/garden/'}  # plus /garden/focus/<id>


def _all_pages(client, user):
    """(path, html) for every GET page, anonymous first then logged in."""
    pages = []
    for path in ('/', '/auth/login', '/auth/register'):
        pages.append((path, client.get(path)))
    user_pages = _authenticated_pages(user)
    _login(client)
    for path in user_pages:
        pages.append((path, client.get(path)))
    return pages


def test_vis_network_loads_only_on_graph_pages(app):
    user = _user()
    client = app.test_client()
    for path, response in _all_pages(client, user):
        assert response.status_code == 200, path
        srcs = [s.get('src') for s in _parse(response.get_data(as_text=True)).scripts]
        wants_vis = path in GRAPH_PAGES or path.startswith('/garden/focus/')
        assert (VIS_SRC in srcs) is wants_vis, path


def test_pages_have_no_inline_script_handlers_or_style_attributes(app):
    user = _user()
    client = app.test_client()
    for path, response in _all_pages(client, user):
        doc = _parse(response.get_data(as_text=True))
        for script in doc.scripts:
            assert script.get('src') or script.get('type') == 'application/json', (path, script)
        for tag, attrs in doc.elements:
            handlers = [name for name in attrs if name.startswith('on')]
            assert not handlers, (path, tag, handlers)
            assert 'style' not in attrs, (path, tag, attrs.get('style'))


def _csp(response):
    header = response.headers.get('Content-Security-Policy')
    assert header, 'missing Content-Security-Policy'
    return {d.split()[0]: d.split()[1:] for d in (p.strip() for p in header.split(';')) if d}


def test_csp_is_strict_on_html_and_json_responses(app):
    user = _user()
    client = app.test_client()
    responses = [r for _, r in _all_pages(client, user)]
    responses.append(client.get('/garden/data'))
    responses.append(client.get('/does-not-exist'))
    for response in responses:
        policy = _csp(response)
        assert policy['script-src'] == ["'self'"]
        style = policy['style-src']
        assert style[0] == "'self'" and all(v.startswith("'sha256-") for v in style[1:])
        assert 'style-src-attr' not in policy and 'style-src-elem' not in policy
        assert policy['object-src'] == ["'none'"]
        assert policy['base-uri'] == ["'self'"]
        assert policy['frame-ancestors'] == ["'none'"]
        assert policy['form-action'] == ["'self'"]
        assert policy['default-src'] == ["'self'"]
        assert not any("'unsafe" in v for values in policy.values() for v in values)
