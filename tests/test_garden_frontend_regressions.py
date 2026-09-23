"""Source-level regression guards for two garden UI fixes that have no
other automated coverage: vis-network's default click-selection style
silently overriding a node's real color, and Bootstrap's stock blue
focus ring on buttons.

Both fixes live entirely in front-end assets (main.js, style.css) that
render behavior only a real browser can exercise - this project has no
browser-test infrastructure (no pytest-playwright, no JS test runner),
and adding one is out of scope for a "keep these fixes from silently
regressing" test. These are deliberately static/structural checks: they
parse the actual shipped source and assert the specific patterns that
make each fix work are still present, in the specific places they need
to be. They will catch someone deleting or moving the fix; they will
NOT catch a real browser rendering it wrong despite the source looking
correct - that still needs the manual Playwright verification the
CLAUDE.md audit entries describe.
"""

import os
import re

APP_STATIC = os.path.join(os.path.dirname(__file__), '..', 'app', 'static')
MAIN_JS_PATH = os.path.join(APP_STATIC, 'js', 'main.js')
STYLE_CSS_PATH = os.path.join(APP_STATIC, 'css', 'style.css')


def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def _function_source(js_source, function_name):
    """Extract one top-level `function name(...) { ... }` block's source
    by slicing from its declaration to the next top-level `function`
    declaration (or end of file). Good enough for this file's flat,
    non-nested function layout - not a real JS parser."""
    start_match = re.search(r'^function ' + re.escape(function_name) + r'\(', js_source, re.MULTILINE)
    assert start_match, f'function {function_name}() not found in main.js'
    rest = js_source[start_match.end():]
    next_match = re.search(r'^function \w+\(', rest, re.MULTILINE)
    end = start_match.end() + (next_match.start() if next_match else len(rest))
    return js_source[start_match.start():end]


# ---- node click preserving category/pinned colors ----
# (see CLAUDE.md's audit entries: vis-network's default `chosen` selection
# style used to replace a clicked node's real color/border with a flat
# blue highlight, wiping the category ring and the pinned gold ring on the
# single most common interaction with the graph)

def test_render_graph_disables_default_chosen_style():
    source = _function_source(_read(MAIN_JS_PATH), 'renderGraph')
    assert 'chosen: false' in source, (
        "renderGraph()'s node options must set chosen:false, or "
        'vis-network silently overrides clicked nodes with a flat blue '
        'highlight instead of their real category/pinned color.'
    )


def test_render_focus_graph_disables_default_chosen_style():
    source = _function_source(_read(MAIN_JS_PATH), 'renderFocusGraph')
    assert 'chosen: false' in source, (
        "renderFocusGraph()'s node options must set chosen:false too - "
        'the focus view has the same click-to-select behavior as the '
        'main graph and is just as vulnerable to the same override.'
    )


def test_neighborhood_highlight_dims_the_object_shaped_node_color():
    # get_category_color() returns {background, border}, not a flat hex
    # string (needed so pinned notes can get a different border color
    # than their category fill). The dim-on-click logic has to address
    # both sub-fields explicitly, or dimming a non-connected node will
    # either throw on a string method call or silently no-op.
    source = _function_source(_read(MAIN_JS_PATH), 'highlightGardenNeighborhood')
    assert 'node.color.background' in source
    assert 'node.color.border' in source


# ---- focus-ring override (Bootstrap's stock blue -> the app's forest green) ----

def test_btn_focus_visible_overrides_bootstraps_stock_focus_ring():
    css = _read(STYLE_CSS_PATH)
    match = re.search(r'\.btn:focus-visible\s*\{([^}]*)\}', css)
    assert match, (
        '.btn:focus-visible rule not found in style.css - without it, '
        "buttons fall back to Bootstrap's own .btn:focus-visible rule, "
        'which composes its box-shadow from a per-variant hardcoded RGB '
        "the app's --primary-rgb remap never reaches, showing stock blue."
    )
    body = match.group(1)
    assert 'box-shadow' in body
    assert '--primary-rgb' in body, (
        'the focus-ring box-shadow must reference --primary-rgb (the '
        "app's forest green) rather than a hardcoded color or Bootstrap's "
        'own --bs-btn-focus-shadow-rgb chain, which a previous attempt at '
        'this fix showed does not reliably reach real button variants.'
    )
