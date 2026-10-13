"""Thought Garden's shared design for the Streamlit port.

The Flask app and this port draw from one design package, `tg_ui` at the
repo root: tokens, category palette, flower illustrations, the note
macros and the garden itself. This module is the port's only bridge to it:

- apply_theme()   loads the shared stylesheets into the page (st.html with
                  only <style> content, which Streamlit puts in the event
                  container, so it takes no space)
- hero(), section()            page banners/headings in the Flask style
- note_card(), note_row(), journal()   the shared Jinja macros as HTML
- garden()        the full Knowledge Garden as a component whose root is
                  tg_ui/static, running the same JS/CSS as the Flask page

Styling only ever targets our own markup (.tg-*) and containers we create
with a `key` (st-key-<key>), never Streamlit's generated class names.

Added in the Phase 6 design pass (2026-10-12); see docs/STREAMLIT_DESIGN.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from functools import lru_cache

import streamlit as st
import streamlit.components.v1 as components

# tg_ui lives at the repo root, two levels up. Appended (not prepended) so
# this port's own `app` and `config` packages keep winning their imports.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.append(_REPO_ROOT)

import tg_ui  # noqa: E402
from tg_ui import categories as palette  # noqa: E402
from tg_ui import flowers, presenters, render  # noqa: E402

_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_CSS_FILES = ("tokens.css", "categories.css", "labels.css", "notes.css", "streamlit.css")
_CANOPY_PHOTO = "img/botanical/foliage-palms-sm.webp"

# One flower medallion per growth stage label, in the order growth happens.
STAGES = flowers.STAGES
STAGE_LABELS = flowers.STAGE_LABELS

_garden_component = components.declare_component("tg_garden", path=tg_ui.STATIC_DIR)


# ---------------------------------------------------------------------------
# theme
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _theme_css() -> str:
    parts = []
    for name in _CSS_FILES:
        with open(os.path.join(tg_ui.STATIC_DIR, "css", name), encoding="utf-8") as fh:
            # Comments go: smaller payload, and Streamlit's HTML sanitizer
            # (DOMPurify) drops a whole <style> whose text has "<" + letter.
            parts.append(_CSS_COMMENT.sub("", fh.read()))
    parts.append(f':root {{ --tg-canopy-photo: url("{render.asset_data_uri(_CANOPY_PHOTO)}"); }}')
    return "<style>\n" + "\n".join(parts) + "\n</style>"


def apply_theme() -> None:
    """Load the shared design into the current page (call once per run)."""
    st.html(_theme_css())


# ---------------------------------------------------------------------------
# categories
# ---------------------------------------------------------------------------

def category_choices(extra: str | None = None) -> list[str]:
    """Values for a category select: none, the palette presets, 'Other',
    plus `extra` (a note's current custom category) when it isn't one."""
    values = [""] + [value for value, _label, _group in palette.presets()] + ["Other"]
    if extra and extra not in values:
        values.append(extra)
    return values


def category_label(value: str | None) -> str:
    """'Writing  ·  Rose'-style option text for a category select."""
    if not value:
        return "Choose a category"
    c = palette.resolve(value)
    label = c["label"] if c and c["value"] == value else value
    return f"{label}  ·  {flowers.flower_name(palette.flower(value))}"


def display_category(value: str | None) -> str:
    return palette.display_name(value)


# ---------------------------------------------------------------------------
# note presentation (shared macros)
# ---------------------------------------------------------------------------

def view(note, stage: str | None = None, connections: int | None = None) -> dict:
    return presenters.note_view(note, stage=stage, connections=connections)


def hero(eyebrow: str, title: str, lead: str | None = None, stats: list[tuple[str, int]] | None = None) -> None:
    html = render.environment().from_string(
        '<section class="tg-st-hero"><p class="tg-st-eyebrow">{{ eyebrow }}</p><h1>{{ title }}</h1>'
        '{% if lead %}<p class="tg-st-lead">{{ lead }}</p>{% endif %}'
        '{% if stats %}<dl class="tg-st-stats">{% for label, value in stats %}'
        '<div><dt>{{ label }}</dt><dd>{{ value }}</dd></div>{% endfor %}</dl>{% endif %}</section>'
    ).render(eyebrow=eyebrow, title=title, lead=lead, stats=stats)
    st.html(html)


def section(title: str, hint: str | None = None) -> None:
    st.html(render.environment().from_string(
        '<div class="tg-st-section"><h2>{{ title }}</h2>{% if hint %}<p>{{ hint }}</p>{% endif %}</div>'
    ).render(title=title, hint=hint))


def note_card(vm: dict) -> None:
    st.html(render.render("note_card", vm, heading="h3"))


def note_row(vm: dict, excerpt: int = 96) -> None:
    st.html(render.render("note_row", vm, excerpt=max(excerpt, 1), show_excerpt=excerpt > 0))


def flowerbeds(rows) -> None:
    """(category, count) rows, each led by its category's flower."""
    beds = [{"label": palette.display_name(c), "badge": palette.badge_class(c),
             "hue": f"tg-hue-{palette.slug(c)}", "plant": flowers.plant_filename(c, "tree"), "count": n}
            for c, n in rows]
    st.html(render.environment().from_string(
        '<ul class="tg-beds">{% for b in beds %}<li class="{{ b.hue }}">'
        '<span class="tg-plant tg-plant--sm {{ b.hue }}"><img src="{{ tg_asset(b.plant) }}" alt="" width="64" height="64"></span>'
        '<span class="badge {{ b.badge }}">{{ b.label }}</span>'
        '<span class="tg-beds-count">{{ b.count }} note{{ "s" if b.count != 1 }}</span></li>{% endfor %}</ul>'
    ).render(beds=beds))


def journal(vm: dict) -> None:
    """The journal header for a note (plant, title, meta, tags); the page
    renders the Markdown body itself with st.markdown underneath."""
    st.html(render.render("journal", vm, body=""))


def connection_row(vm: dict, label: str, reason: str) -> None:
    st.html(render.environment().from_string(
        '<div class="tg-st-connection">'
        '<span class="tg-plant tg-plant--sm {{ vm.hue_class }}"><img src="{{ tg_asset(vm.plant) }}" alt="" width="64" height="64"></span>'
        '<div><strong>{{ vm.title }}</strong> <span class="badge {{ badge }}">{{ label }}</span>'
        '<small>{{ reason }}</small></div></div>'
    ).render(vm=vm, label=label, reason=reason,
             badge="bg-success" if label == "Strong match" else "bg-secondary"))


# ---------------------------------------------------------------------------
# the garden
# ---------------------------------------------------------------------------

def garden(payload: dict, *, height: int = 760, key: str = "tggarden-frame"):
    """Render the Knowledge Garden. `payload` is streamlit_garden_ops'
    {'nodes', 'edges', 'notes', 'categories'}. Returns the last action the
    user took in it ({'action', 'id', 'nonce'}) or None."""
    present = payload.get("categories") or []
    cats = [m for m in palette.metadata(present) if m["value"] in present]
    counts: dict[str, int] = {}
    for node in payload["nodes"]:
        counts[node["category"]] = counts.get(node["category"], 0) + 1
    common = max(counts, key=counts.get) if counts else None
    markup = str(render.macro("garden", "tg/garden.html", inline_assets=False)(
        cats,
        presenters.flower_key(c["value"] for c in cats),
        {"list": None, "create": None},
        user_id=payload.get("user_id", ""),
        growth_flower=palette.flower(common) if common else "wildflower",
    ))
    data = {
        "markup": markup,
        "categories": palette.metadata(present),
        "nodes": payload["nodes"],
        "edges": payload["edges"],
        "notes": {str(k): v for k, v in payload.get("notes", {}).items()},
        "frame_height": height,
    }
    data["render_key"] = hashlib.sha1(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    with st.container(key="tggarden"):
        return _garden_component(**data, key=key, default=None, height=height)
