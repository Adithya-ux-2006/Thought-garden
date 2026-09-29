"""Runs main.js's garden note panel in Node against a minimal fake DOM and
checks that user-controlled note data is rendered as text, never parsed as
HTML. Skipped when Node isn't installed."""

import json
import os
import shutil
import subprocess

import pytest

MAIN_JS = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'js', 'main.js')
NODE = shutil.which('node')

PAYLOAD = '<img src=x onerror=alert(1)>'

HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const note = JSON.parse(process.argv[1]);
const htmlWrites = [];
const fetched = [];

class El {
  constructor(tag, id) {
    this.tagName = tag; this.id = id; this.children = []; this._text = '';
    this.className = ''; this.listeners = {}; this.style = {}; this.href = '';
    this.classList = { add() {}, remove() {} };
  }
  set innerHTML(v) { htmlWrites.push(String(v)); this.children = []; this._text = ''; }
  get innerHTML() { return ''; }
  set textContent(v) { this.children = []; this._text = String(v); }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(''); }
  appendChild(c) { this.children.push(c); return c; }
  append(...cs) { cs.forEach(c => this.children.push(typeof c === 'string' ? { textContent: c } : c)); }
  replaceChildren(...cs) { this.children = []; this._text = ''; this.append(...cs); }
  addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
  querySelector() { return new El('div'); }
}

const byId = {};
const document = {
  getElementById: id => (byId[id] = byId[id] || new El('div', id)),
  createElement: tag => new El(tag),
  addEventListener() {},
  querySelectorAll: () => [],
  documentElement: { getAttribute: () => null },
};
const fetch = url => { fetched.push(url); return Promise.resolve({ json: () => Promise.resolve(note) }); };

const ctx = vm.createContext({
  document, fetch, console, window: {}, setTimeout, clearTimeout,
  localStorage: { getItem() { return null; }, setItem() {} },
  getComputedStyle: () => ({ getPropertyValue: () => '' }),
});
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'), ctx);

const tick = () => new Promise(r => setImmediate(r));
function findWithListener(el) {
  if (el.listeners && el.listeners.click) return el;
  for (const c of el.children || []) { const f = findWithListener(c); if (f) return f; }
  return null;
}

(async () => {
  ctx.showNotePanel(note.id);
  for (let i = 0; i < 5; i++) await tick();
  const connections = document.getElementById('panelConnections');
  const clickable = findWithListener(connections);
  if (clickable) clickable.listeners.click.forEach(fn => fn({}));
  for (let i = 0; i < 5; i++) await tick();
  console.log(JSON.stringify({
    htmlWrites,
    fetched,
    tagsText: document.getElementById('panelTags').textContent,
    connectionsText: connections.textContent,
  }));
})();
"""


def _render_panel(note):
    if NODE is None:
        pytest.skip('Node.js not installed')
    proc = subprocess.run(
        [NODE, '-e', HARNESS, json.dumps(note), os.path.abspath(MAIN_JS)],
        capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _note(connections):
    return {
        'id': 1, 'title': PAYLOAD, 'content': PAYLOAD, 'category': PAYLOAD,
        'tags': [PAYLOAD, 'plain'], 'created_at': '2026-09-24T00:00:00',
        'connections': connections,
    }


def test_panel_renders_user_content_as_text_not_html():
    result = _render_panel(_note([
        {'id': 7, 'title': PAYLOAD, 'category': PAYLOAD, 'similarity': 0.9,
         'label': 'Strong match', 'reason': f'Shared tags: {PAYLOAD}.'},
    ]))

    assert not [h for h in result['htmlWrites'] if '<img' in h], result['htmlWrites']
    assert PAYLOAD in result['tagsText']
    assert 'plain' in result['tagsText']
    assert PAYLOAD in result['connectionsText']
    assert 'Strong match' in result['connectionsText']
    assert f'Shared tags: {PAYLOAD}.' in result['connectionsText']


def test_panel_connection_click_opens_that_note():
    result = _render_panel(_note([
        {'id': 7, 'title': 'Other note', 'category': None, 'similarity': 0.5,
         'label': 'Related', 'reason': 'Similar overall meaning.'},
    ]))

    assert result['fetched'] == ['/garden/note/1', '/garden/note/7']
    assert 'Uncategorized' in result['connectionsText']


def test_panel_without_connections_shows_empty_message():
    result = _render_panel(_note([]))

    assert 'No connections found' in result['connectionsText']
