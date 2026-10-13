"""The shared design package (tg_ui): generated assets stay fresh, the
palette stays readable, view models and macros stay safe, and the Flask
pages render through it. tg_ui is also what the Streamlit port loads, so
these guard both frontends."""

import os
import re
import subprocess
import sys

import pytest

from app import create_app, db
from app.models import Note, Relationship, Tag, User
from tg_ui import STATIC_DIR, build, categories, flowers, presenters, render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# generated assets + palette
# ---------------------------------------------------------------------------

def test_generated_category_css_is_fresh():
    with open(build.CSS_PATH, encoding='utf-8') as fh:
        assert fh.read() == build.categories_css(), 'run `python -m tg_ui.build`'


def test_generated_plants_are_fresh_and_complete():
    expected = build.plant_files()
    assert len(expected) == len(flowers.FLOWERS) * len(flowers.STAGES)
    for name, svg in expected.items():
        with open(os.path.join(build.PLANT_DIR, name), encoding='utf-8') as fh:
            assert fh.read() == svg, f'{name} is stale - run `python -m tg_ui.build`'


def _luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contrast(a, b):
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


@pytest.mark.parametrize('category', categories.CATEGORIES, ids=lambda c: c['slug'])
def test_category_badges_meet_aa_in_both_themes(category):
    assert _contrast(category['light']['soft_text'], category['light']['soft_bg']) >= 4.5
    assert _contrast(category['dark']['soft_text'], category['dark']['soft_bg']) >= 4.5


def test_every_category_has_a_flower_and_unique_slug():
    slugs = [c['slug'] for c in categories.CATEGORIES]
    assert len(slugs) == len(set(slugs))
    assert all(c['flower'] in flowers.FLOWERS for c in categories.CATEGORIES)


def test_existing_categories_keep_their_values_and_colors():
    # Stored notes use these exact values; nothing may be remapped.
    by_value = {c['value']: c for c in categories.CATEGORIES}
    assert {'AI', 'Research', 'Study'} <= set(by_value)
    assert categories.color('Research') == {'background': '#6f9db5', 'border': '#3d5663'}


def test_retired_technical_categories_read_as_study_without_renaming():
    # Software Engineering / Cybersecurity / Operating Systems are no longer
    # presets; notes that still store them keep their text and look like Study.
    values = {c['value'] for c in categories.CATEGORIES}
    for old in ('Software Engineering', 'Cybersecurity', 'Operating Systems'):
        assert old not in values
        assert categories.slug(old) == 'study'
        assert categories.flower(old) == 'bluebell'
        assert categories.display_name(old) == old


def test_categories_resolve_aliases_case_and_unknowns():
    assert categories.flower('Writing') == 'rose'
    assert categories.flower('writing') == 'rose'
    assert categories.flower('Ideas') == 'daisy'       # old preset borrows Creativity's flower
    assert categories.slug('Learning') == 'study'
    assert categories.slug('Study Material') == 'study'
    assert categories.flower('Travel') == 'wildflower'
    assert categories.badge_class('Travel') == 'badge-category-none'
    assert categories.display_name(None) == 'Wild thoughts'
    assert categories.display_name('Uncategorized') == 'Wild thoughts'
    assert categories.display_name('Travel') == 'Travel'


def test_plant_filename_falls_back_safely():
    assert flowers.plant_filename('AI', 'tree') == 'img/plants/orchid-tree.svg'
    assert flowers.plant_filename(None, 'not-a-stage') == 'img/plants/wildflower-seed.svg'


def test_shared_css_is_safe_for_streamlit_html():
    # Streamlit's st.html sanitizer (DOMPurify) drops an entire <style> whose
    # text contains "<" followed by a word character or "/". The port's
    # streamlit_ui.apply_theme() strips comments first; the rules themselves
    # must never contain one.
    for name in ('tokens.css', 'categories.css', 'labels.css', 'notes.css', 'streamlit.css'):
        with open(os.path.join(STATIC_DIR, 'css', name), encoding='utf-8') as fh:
            rules = re.sub(r'/\*.*?\*/', '', fh.read(), flags=re.S)
        assert not re.search(r'<[/\w]', rules), name


def test_garden_component_page_references_existing_files():
    with open(os.path.join(STATIC_DIR, 'index.html'), encoding='utf-8') as fh:
        page = fh.read()
    refs = re.findall(r'(?:href|src)="([^"]+)"', page)
    assert refs
    for ref in refs:
        assert os.path.isfile(os.path.join(STATIC_DIR, ref)), ref


def test_tg_ui_imports_neither_frontend():
    # The Streamlit port appends the repo root to sys.path and imports tg_ui;
    # if tg_ui pulled in Flask's `app` it would shadow the port's own.
    code = ('import sys, tg_ui.presenters, tg_ui.render, tg_ui.build; '
            'print(",".join(m for m in ("app", "flask", "streamlit") if m in sys.modules))')
    out = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == ''


# ---------------------------------------------------------------------------
# presenters + macros
# ---------------------------------------------------------------------------

class _Tag:
    def __init__(self, name):
        self.name = name


class _Note:
    def __init__(self, **kw):
        from datetime import datetime, timezone
        self.id = kw.get('id', 1)
        self.title = kw.get('title', 'A title')
        self.content = kw.get('content', 'Some *content* here.')
        self.category = kw.get('category')
        self.tags = [_Tag(t) for t in kw.get('tags', [])]
        self.created_at = kw.get('created_at', datetime(2026, 1, 2, tzinfo=timezone.utc))
        self.updated_at = kw.get('updated_at', self.created_at)
        self.is_pinned = kw.get('is_pinned', False)
        self.is_archived = kw.get('is_archived', False)


def test_plain_text_strips_markdown_for_previews():
    text = presenters.plain_text('# Heading\n\nSome **bold** and a [link](http://x) and `code`.\n\n```\nskip\n```')
    assert text == 'Heading Some bold and a link and code.'


def test_note_view_hides_tag_equal_to_category_and_counts_reading_time():
    vm = presenters.note_view(_Note(category='AI', tags=['ai', 'Research'], content='word ' * 450), stage='sapling')
    assert vm['shown_tags'] == ['Research']
    assert vm['minutes'] == 3
    assert vm['plant'] == 'img/plants/orchid-sapling.svg'
    assert vm['stage_label'] == 'Sapling'


PAYLOAD = '<script>alert(1)</script>'


@pytest.mark.parametrize('macro', ['note_card', 'note_row', 'journal'])
def test_macros_escape_user_content_and_use_no_inline_styles(macro):
    vm = presenters.note_view(_Note(title=PAYLOAD, content=PAYLOAD, category=PAYLOAD, tags=[PAYLOAD]),
                              stage='seed')
    html = render.render(macro, vm)
    assert '<script' not in html
    assert '&lt;script&gt;' in html
    # Flask's CSP forbids style="" attributes; the macros never emit them.
    assert not re.search(r'\sstyle=', html)


# ---------------------------------------------------------------------------
# Flask pages through tg_ui
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                      'WTF_CSRF_ENABLED': False, 'SECRET_KEY': 'test-secret-key'})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def garden_client(app):
    user = User(name='Gardener', email='g@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.flush()
    a = Note(user_id=user.id, title='Rose story', content='A story about roses.', category='Writing')
    b = Note(user_id=user.id, title='Wild idea', content='No category at all.', category=None)
    c = Note(user_id=user.id, title='Travel log', content='Lisbon trams.', category='Travel')
    db.session.add_all([a, b, c])
    db.session.flush()
    a.tags = [Tag(user_id=user.id, name='story idea')]
    db.session.add(Relationship(source_note_id=a.id, target_note_id=b.id, similarity_score=0.5))
    db.session.commit()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    return client


def test_garden_data_adds_each_notes_flower(garden_client):
    data = garden_client.get('/garden/data').get_json()
    by_title = {n['title']: n for n in data['nodes']}
    assert by_title['Rose story']['flower'] == 'rose'
    assert by_title['Wild idea']['flower'] == 'wildflower'
    assert by_title['Travel log']['plant'].startswith('img/plants/wildflower-')
    for node in data['nodes']:
        assert os.path.isfile(os.path.join(STATIC_DIR, node['plant']))
        assert node['image'].startswith('/static/img/garden/')  # existing field unchanged


def test_garden_page_offers_chips_only_for_categories_in_the_garden(garden_client):
    html = garden_client.get('/garden/').get_data(as_text=True)
    chips = re.findall(r'class="form-check-input garden-category-filter"[^>]*value="([^"]*)"', html)
    assert sorted(chips) == ['Travel', 'Uncategorized', 'Writing']
    assert 'Wild thoughts' in html
    assert 'img/plants/rose-tree.svg' in html  # legend's flower key


def test_notes_list_and_dashboard_render_shared_note_markup(garden_client):
    notes_html = garden_client.get('/notes/').get_data(as_text=True)
    assert notes_html.count('tg-note--editorial') == 3
    assert 'img/plants/rose-' in notes_html
    dash_html = garden_client.get('/dashboard').get_data(as_text=True)
    assert 'tg-note--compact' in dash_html
    assert 'Your flowerbeds' in dash_html


def test_composer_enhances_category_and_tags(garden_client):
    html = garden_client.get('/notes/create').get_data(as_text=True)
    assert 'data-picker-kind="category"' in html and 'data-picker-custom' in html
    assert 'data-tag-input' in html
    assert re.search(r'<script type="application/json" id="userTags">\["story idea"\]</script>', html)


def test_custom_category_round_trips_through_the_form(garden_client):
    response = garden_client.post('/notes/create', data={
        'title': 'Field notes', 'content': 'Birdsong at dawn.', 'category': 'Nature walks', 'tags': 'observation',
    }, follow_redirects=True)
    assert response.status_code == 200
    note = Note.query.filter_by(title='Field notes').one()
    assert note.category == 'Nature walks'
    assert 'img/plants/wildflower-' in response.get_data(as_text=True)
