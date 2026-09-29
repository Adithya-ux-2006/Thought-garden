"""Browser smoke tests: the real app in Chromium, with CSRF and CSP enforced.

Skipped when Playwright or its Chromium build is not installed
(`pip install playwright && python -m playwright install chromium`).
"""
import threading
from datetime import timedelta

import pytest

playwright_sync = pytest.importorskip('playwright.sync_api')

from werkzeug.serving import make_server

from app import create_app, db
from app.models import Note, Relationship, Tag, User, utcnow

PASSWORD = 'password123'
EMAIL = 'smoke@example.com'
FOREST_GREEN_RGB = '25, 60, 50'


@pytest.fixture(scope='module')
def browser():
    with playwright_sync.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # browser binaries not installed
            pytest.skip(f'Chromium unavailable: {exc}')
        yield browser
        browser.close()


@pytest.fixture
def live(tmp_path):
    """A seeded app served on a random local port. Function-scoped so the
    conftest ML/thread stubs apply while it serves."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{(tmp_path / 'smoke.db').as_posix()}",
        'WTF_CSRF_ENABLED': True,
        'SECRET_KEY': 'smoke-secret-key',
    })
    with app.app_context():
        db.create_all()
        seed = _seed()
    server = make_server('127.0.0.1', 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield {'url': f'http://127.0.0.1:{server.server_port}', 'app': app, **seed}
    server.shutdown()
    thread.join(timeout=5)
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def _seed():
    user = User(name='Smoke', email=EMAIL)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()

    def note(title, content, category, **kw):
        n = Note(user_id=user.id, title=title, content=content, category=category, **kw)
        db.session.add(n)
        return n

    hub = note('Neural networks', 'Backpropagation trains neural networks.', 'AI', is_pinned=True,
               created_at=utcnow() - timedelta(days=3))
    spoke = note('Gradient descent', 'Gradient descent drives backpropagation.', 'AI')
    loner = note('Kernel scheduling', 'Round robin scheduling in kernels.', 'Operating Systems')
    xss = note('Markdown sample',
               '# Heading\n\n**bold** and `code`\n\n<script>window.__pwned = 1</script>\n\n'
               '<img src=x onerror="window.__pwned = 1">\n\n[click](javascript:window.__pwned=1)\n',
               'Research')
    db.session.flush()
    shared = Tag(user_id=user.id, name='Deep-Learning')
    hub.tags = [shared]
    spoke.tags = [shared, Tag(user_id=user.id, name='Optimisation')]
    db.session.add(Relationship(source_note_id=hub.id, target_note_id=spoke.id, similarity_score=0.8,
                                relationship_type='semantic', method='keyword'))
    db.session.commit()
    return {'hub': hub.id, 'spoke': spoke.id, 'loner': loner.id, 'xss': xss.id}


class _Page:
    """A browser page that records console errors, page errors and CSP violations."""

    def __init__(self, browser, base_url, init_script=None):
        self.context = browser.new_context(base_url=base_url)
        if init_script:
            self.context.add_init_script(init_script)
        self.page = self.context.new_page()
        self.problems = []
        self.page.on('console', self._console)
        self.page.on('pageerror', lambda exc: self.problems.append(f'pageerror: {exc}'))

    def _console(self, message):
        if message.type == 'error' and 'favicon.ico' not in (message.location or {}).get('url', ''):
            self.problems.append(f'console: {message.text}')

    def login(self):
        self.page.goto('/auth/login')
        self.page.fill('input[name="email"]', EMAIL)
        self.page.fill('input[name="password"]', PASSWORD)
        self.page.click('button[type="submit"], input[type="submit"]')
        self.page.wait_for_url('**/dashboard')
        return self

    def close(self):
        self.context.close()


@pytest.fixture
def ui(browser, live):
    pages = []

    def make(init_script=None, login=True):
        p = _Page(browser, live['url'], init_script)
        pages.append(p)
        return p.login() if login else p

    yield make
    for p in pages:
        p.close()


def _wait_until(page, expression, timeout_ms=10000):
    """Poll `expression` via page.evaluate. Playwright's wait_for_function
    evaluates string predicates in-page, which the app's CSP (correctly) blocks."""
    waited = 0
    while not page.evaluate(expression):
        if waited >= timeout_ms:
            raise AssertionError(f'timed out waiting for: {expression}')
        page.wait_for_timeout(100)
        waited += 100


def _wait_for_stable_graph(page, network_var):
    _wait_until(page, f'typeof {network_var} !== "undefined" && {network_var} !== null')
    if network_var == 'gardenNetwork':
        # main.js disables physics (and unticks the toggle) once stabilized.
        _wait_until(page, "document.getElementById('physicsToggle').checked === false")
    else:
        page.wait_for_timeout(1500)


def _node_ring_pixel(page, network_var, node_id):
    """RGBA of the canvas pixel on the top of a node's border ring, plus the
    node's DOM position so the caller can click it."""
    return page.evaluate(
        """([networkName, id]) => {
            // Top-level `let` bindings from main.js aren't window properties.
            const network = {gardenNetwork, focusNetwork}[networkName];
            const canvas = network.canvas.frame.canvas;
            const node = network.body.nodes[id];
            const center = network.canvasToDOM(network.getPositions([id])[id]);
            const ringTop = network.canvasToDOM({x: node.x, y: node.y - node.shape.radius});
            const ratio = canvas.width / canvas.clientWidth;
            const pixel = canvas.getContext('2d').getImageData(
                Math.round(ringTop.x * ratio), Math.round((ringTop.y + 1) * ratio), 1, 1).data;
            const box = canvas.getBoundingClientRect();
            return {rgba: Array.from(pixel), x: box.left + center.x, y: box.top + center.y};
        }""",
        [network_var, node_id],
    )


# ---------------------------------------------------------------------------
# CSP, script loading, theme
# ---------------------------------------------------------------------------

def test_every_page_loads_without_csp_violations_or_script_errors(ui, live):
    anon = ui(login=False)
    anon.page.goto('/')
    anon.page.wait_for_load_state('networkidle')
    assert anon.page.locator('#heroGraph svg circle').count() == 6
    assert anon.page.evaluate('typeof window.vis') == 'undefined'
    assert anon.problems == []

    session = ui()
    graph_pages = {'/garden/', f"/garden/focus/{live['hub']}"}
    for path in ['/dashboard', '/notes/', f"/notes/{live['hub']}", f"/notes/{live['hub']}/edit",
                 '/notes/create', '/garden/', '/garden/list', f"/garden/focus/{live['hub']}",
                 '/search/?q=gradient', '/insights', '/auth/profile']:
        session.page.goto(path)
        session.page.wait_for_load_state('networkidle')
        has_vis = session.page.evaluate('typeof window.vis') == 'object'
        assert has_vis is (path in graph_pages), path
        assert session.problems == [], path


def test_saved_dark_theme_applies_before_main_js_runs(ui, live):
    session = ui(init_script="localStorage.setItem('darkMode', 'true')")
    # With main.js blocked, only the <head> script can set the theme.
    session.page.route('**/static/js/main.js', lambda route: route.abort())
    session.page.goto('/notes/')
    assert session.page.evaluate("document.documentElement.getAttribute('data-bs-theme')") == 'dark'


# ---------------------------------------------------------------------------
# Garden graph (replaces the source-grep checks for chosen:false and dimming)
# ---------------------------------------------------------------------------

def test_clicking_a_garden_node_keeps_its_colors_and_dims_unrelated_nodes(ui, live):
    session = ui()
    page = session.page
    page.goto('/garden/')
    _wait_for_stable_graph(page, 'gardenNetwork')
    page.mouse.move(5, 5)

    hub = live['hub']
    before = _node_ring_pixel(page, 'gardenNetwork', hub)
    page.mouse.click(before['x'], before['y'])
    page.wait_for_selector('#panelContent:not(.d-none)')
    page.wait_for_timeout(300)
    after = _node_ring_pixel(page, 'gardenNetwork', hub)

    # vis's default "chosen" styling would recolour/thicken the selected
    # node's ring; the pinned gold ring must render exactly as before.
    assert after['rgba'] == before['rgba']

    colors = page.evaluate('Object.fromEntries(gardenNodesDataSet.get().map(n => [n.id, n.color]))')
    assert colors[str(hub)]['border'].lower() == '#a57834'
    assert colors[str(live['spoke'])]['background'].startswith('#'), 'connected node stays undimmed'
    assert colors[str(live['loner'])]['background'].endswith('0.12)'), 'unrelated node is dimmed'
    assert session.problems == []


def test_garden_panel_explains_connections_and_buttons_work(ui, live):
    session = ui()
    page = session.page
    page.goto('/garden/')
    _wait_for_stable_graph(page, 'gardenNetwork')

    hub = _node_ring_pixel(page, 'gardenNetwork', live['hub'])
    page.mouse.click(hub['x'], hub['y'])
    connection = page.locator('#panelConnections .connection-item').first
    connection.wait_for()
    assert 'Shared tags: Deep-Learning' in connection.inner_text()
    assert connection.evaluate('el => el.tagName') == 'BUTTON'

    page.get_by_role('button', name='Close note details').click()
    assert page.locator('#panelContent').get_attribute('class').split().count('d-none') == 1

    page.get_by_role('button', name='Fit to view').click()
    page.get_by_role('button', name='Reset view').click()
    page.get_by_label('Find a note in the graph').fill('gradient')
    page.keyboard.press('Enter')
    _wait_until(page, "document.getElementById('searchFeedback').textContent.trim() !== ''")
    assert session.problems == []


def test_clicking_a_focus_graph_node_keeps_its_colors(ui, live):
    session = ui()
    page = session.page
    page.goto(f"/garden/focus/{live['hub']}")
    _wait_for_stable_graph(page, 'focusNetwork')
    page.evaluate('focusNetwork.setOptions({physics: {enabled: false}})')
    page.mouse.move(5, 5)
    page.wait_for_timeout(200)

    before = _node_ring_pixel(page, 'focusNetwork', live['hub'])
    page.mouse.click(before['x'], before['y'])
    page.wait_for_timeout(300)
    after = _node_ring_pixel(page, 'focusNetwork', live['hub'])
    assert after['rgba'] == before['rgba']
    assert session.problems == []


# ---------------------------------------------------------------------------
# Keyboard focus ring (replaces the source-grep check on style.css)
# ---------------------------------------------------------------------------

def test_keyboard_focus_ring_on_buttons_is_forest_green(ui, live):
    session = ui()
    page = session.page
    page.goto('/notes/create')
    page.focus('#suggestTagsButton')
    page.keyboard.press('Shift+Tab')
    page.keyboard.press('Tab')  # keyboard-initiated focus => :focus-visible
    page.wait_for_timeout(400)  # Bootstrap transitions box-shadow
    shadow = page.evaluate('getComputedStyle(document.activeElement).boxShadow')
    assert page.evaluate('document.activeElement.id') == 'suggestTagsButton'
    assert FOREST_GREEN_RGB in shadow, shadow


# ---------------------------------------------------------------------------
# Forms, flashes, notes
# ---------------------------------------------------------------------------

def test_delete_from_note_view_asks_first_and_is_csrf_protected(ui, live):
    session = ui()
    page = session.page
    note_url = f"/notes/{live['loner']}"
    page.goto(note_url)

    page.once('dialog', lambda dialog: dialog.dismiss())
    page.get_by_role('button', name='Delete note').click()
    page.wait_for_timeout(300)
    assert page.url.endswith(note_url)

    page.once('dialog', lambda dialog: dialog.accept())
    page.get_by_role('button', name='Delete note').click()
    page.wait_for_url('**/notes/')
    with live['app'].app_context():
        assert db.session.get(Note, live['loner']) is None
    assert session.problems == []


def test_error_flash_persists_while_success_flash_fades(ui, live):
    anon = ui(login=False)
    page = anon.page
    page.clock.install()
    page.goto('/auth/login')
    page.fill('input[name="email"]', EMAIL)
    page.fill('input[name="password"]', 'wrong-password')
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_selector('.alert-danger')
    page.clock.run_for(8000)
    assert page.locator('.alert-danger').is_visible()
    page.get_by_role('button', name='Close').click()
    page.wait_for_selector('.alert-danger', state='detached')

    page.fill('input[name="email"]', EMAIL)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_selector('.alert-success')
    page.clock.run_for(8000)
    page.wait_for_selector('.alert-success', state='detached')


def test_notes_list_filters_submit_on_change(ui, live):
    session = ui()
    page = session.page
    page.goto('/notes/')
    page.get_by_label('Filter by category').select_option('AI')
    page.wait_for_url('**/notes/?category=AI*')
    assert page.locator('.note-card').count() == 2
    assert session.problems == []


def test_tag_suggestion_chips_add_tags(ui, live):
    session = ui()
    page = session.page
    page.goto(f"/notes/{live['hub']}/edit")
    page.get_by_role('button', name='Suggest tags').click()
    chip = page.get_by_role('button', name='Add tag Optimisation')
    chip.click()
    assert page.input_value('input[name="tags"]') == 'Deep-Learning, Optimisation'
    assert chip.count() == 0
    assert session.problems == []


def test_note_markdown_renders_without_running_injected_script(ui, live):
    session = ui()
    page = session.page
    page.goto(f"/notes/{live['xss']}")
    content = page.locator('.note-content')
    assert content.locator('h1').inner_text() == 'Heading'
    assert content.locator('strong').inner_text() == 'bold'
    assert content.locator('script, img').count() == 0
    link = content.get_by_text('click')
    if link.count():
        link.click()
    page.wait_for_timeout(300)
    assert page.evaluate('window.__pwned') is None


def test_garden_list_view_is_keyboard_navigable(ui, live):
    session = ui()
    page = session.page
    page.goto('/garden/')
    page.click('#gardenListLink')
    page.wait_for_url('**/garden/list')

    for _ in range(40):
        page.keyboard.press('Tab')
        if page.evaluate("document.activeElement.textContent.trim()") == 'Gradient descent':
            break
    else:
        pytest.fail('could not reach a note link by keyboard')
    page.keyboard.press('Enter')
    page.wait_for_url(f"**/notes/{live['spoke']}")
    assert session.problems == []
