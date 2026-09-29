from html.parser import HTMLParser

import pytest

from app import create_app, db
from app.models import Note, User
from app.services.markdown_service import ALLOWED_TAGS, render_markdown


class _ElementCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    handle_startendtag = handle_starttag


def _elements(html):
    collector = _ElementCollector()
    collector.feed(str(html))
    return collector.elements


def _assert_inert(html):
    for tag, attrs in _elements(html):
        assert tag in ALLOWED_TAGS, (tag, html)
        for name, value in attrs.items():
            assert not name.startswith('on'), (tag, name, html)
            assert name != 'style', (tag, html)
            if name in ('href', 'src'):
                scheme = (value or '').strip().split(':', 1)[0].lower() if ':' in (value or '') else ''
                assert scheme in ('', 'http', 'https', 'mailto'), (tag, name, value)


# ---- sanitization: nothing executable survives ----

@pytest.mark.parametrize('source', [
    '<script>alert(1)</script>',
    '<SCRIPT SRC=//evil.example/x.js></SCRIPT>',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    '<iframe src="https://evil.example"></iframe>',
    '<a href="javascript:alert(1)">x</a>',
    '<div style="background:url(javascript:alert(1))">x</div>',
    '<object data="x.swf"></object>',
    '<form action="https://evil.example"><button>go</button></form>',
    '<details open ontoggle=alert(1)>',
    '<math><mi xlink:href="javascript:alert(1)">x</mi></math>',
])
def test_raw_html_is_never_emitted_as_markup(source):
    html = render_markdown(source)
    _assert_inert(html)
    assert [tag for tag, _ in _elements(html)] == ['p'], html


@pytest.mark.parametrize('source', [
    '[x](javascript:alert(1))',
    '![x](javascript:alert(1))',
    '[x](<javascript:alert(1)>)',
    '<javascript:alert(1)>',
    '[x]: javascript:alert(1)\n\n[x]',
    '```"><script>alert(1)</script>\ncode\n```',
])
def test_markdown_constructs_never_produce_active_content(source):
    _assert_inert(render_markdown(source))


@pytest.mark.parametrize('href', [
    'javascript:alert(1)',
    'JaVaScRiPt:alert(1)',
    'javascript&#58;alert(1)',
    ' javascript:alert(1)',
    'vbscript:msgbox(1)',
    'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
    'file:///etc/passwd',
])
def test_markdown_links_with_dangerous_schemes_lose_their_href(href):
    html = str(render_markdown(f'[click]({href})')).lower()
    assert 'href="javascript' not in html
    assert 'href=" javascript' not in html
    assert 'href="vbscript' not in html
    assert 'href="data:' not in html
    assert 'href="file:' not in html


def test_markdown_image_with_javascript_src_is_dropped():
    html = str(render_markdown('![x](javascript:alert(1))')).lower()
    assert 'src="javascript' not in html


@pytest.mark.parametrize('raw', [
    '<script>alert(1)</script><p>ok</p>',
    '<img src=x onerror=alert(1)>',
    '<a href="javascript:alert(1)" onclick="x()">x</a>',
    '<a href="  JAVASCRIPT:alert(1)">x</a>',
    '<img src="data:image/svg+xml,<svg onload=alert(1)>">',
    '<p style="position:fixed">x</p>',
    '<iframe srcdoc="<script>alert(1)</script>"></iframe>',
    '<code class="x onmouseover=alert(1)">y</code>',
    '<svg><script>alert(1)</script></svg>',
])
def test_sanitizer_layer_alone_neutralises_raw_html(raw):
    # Defense in depth: holds even if the parser were ever allowed to pass HTML through.
    from app.services.markdown_service import sanitize_html
    _assert_inert(sanitize_html(raw))


def test_code_class_attribute_only_allows_language_hints():
    html = str(render_markdown('```python" onmouseover="alert(1)\nx\n```'))
    assert 'onmouseover' not in html.split('<code')[1].split('>')[0]


# ---- legitimate Markdown still renders ----

def test_common_markdown_renders():
    html = str(render_markdown(
        '# Title\n\n'
        'Some **bold**, *em*, `code` and ~~gone~~.\n\n'
        '- one\n- two\n\n'
        '1. first\n2. second\n\n'
        '> quoted\n\n'
        '```python\nprint("<b>hi</b>")\n```\n\n'
        '| a | b |\n|---|---|\n| 1 | 2 |\n'
    ))
    for fragment in ('<h1>Title</h1>', '<strong>bold</strong>', '<em>em</em>', '<code>code</code>',
                     '<s>gone</s>', '<ul>', '<li>one</li>', '<ol>', '<blockquote>',
                     '<code class="language-python">', '&lt;b&gt;hi&lt;/b&gt;', '<table>', '<td>1</td>'):
        assert fragment in html, (fragment, html)


def test_links_render_with_safe_rel():
    html = str(render_markdown('[docs](https://example.com/a?b=1&c=2)'))
    assert 'href="https://example.com/a?b=1&amp;c=2"' in html
    assert 'rel="noopener noreferrer nofollow"' in html


def test_plain_text_with_angle_brackets_is_preserved_as_text():
    html = str(render_markdown('if a < b and c > d then <maybe>'))
    assert '&lt;' in html and '&gt;' in html
    assert 'maybe' in html


def test_single_newlines_in_plain_text_notes_stay_visible():
    html = str(render_markdown('line one\nline two\n\nnew paragraph'))
    assert html == '<p>line one<br>\nline two</p>\n<p>new paragraph</p>'


def test_empty_and_none_render_to_empty_markup():
    assert str(render_markdown('')) == ''
    assert str(render_markdown(None)) == ''


# ---- wired into the note view ----

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_client(app):
    user = User(name='Md User', email='md@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    client = app.test_client()
    client.post('/auth/login', data={'email': 'md@example.com', 'password': 'password123'})
    return client


def test_note_view_renders_markdown_and_neutralises_html(auth_client, app):
    user = User.query.filter_by(email='md@example.com').one()
    note = Note(user_id=user.id, title='MD', content='**bold** <script>alert("x")</script>')
    db.session.add(note)
    db.session.commit()

    body = auth_client.get(f'/notes/{note.id}').get_data(as_text=True)
    assert '<strong>bold</strong>' in body
    assert '<script>alert' not in body
    assert '&lt;script&gt;' in body
