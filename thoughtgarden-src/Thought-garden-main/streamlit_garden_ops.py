"""Garden graph ops — Streamlit port of Flask app/garden/routes.py.

Builds the same node/edge payloads the Flask `/garden/data` and
`/garden/api/focus/<id>` endpoints return, then renders them with the
vendored vis-network build (inlined, no CDN, no Flask server needed).
Growth-stage SVGs are embedded as data URIs since there is no /static
route in the Streamlit process.
"""

from __future__ import annotations

import base64
import json
import os

import streamlit as st

from streamlit_db import app_context

_ROOT = os.path.dirname(os.path.abspath(__file__))
_VIS_PATH = os.path.join(
    _ROOT, "app", "static", "vendor", "vis-network", "9.1.9", "vis-network.min.js"
)
_ICON_DIR = os.path.join(_ROOT, "app", "static", "img", "garden")

# Matches --pinned-color in app/static/css/style.css — a single value that
# has to read as "pinned" on both a cream and a near-black canvas (same
# reasoning as Flask's PINNED_BORDER_COLOR).
PINNED_BORDER_COLOR = "#a57834"

_CATEGORY_COLORS = {
    "AI": {"background": "#a99bea", "border": "#5c5580"},
    "Artificial Intelligence": {"background": "#a99bea", "border": "#5c5580"},
    "Cybersecurity": {"background": "#e58b78", "border": "#7d4c42"},
    "Software Engineering": {"background": "#6faf8f", "border": "#3d604e"},
    "Operating Systems": {"background": "#d9a441", "border": "#775a23"},
    "Research": {"background": "#6f9db5", "border": "#3d5663"},
}
_FALLBACK_COLOR = {"background": "#d99a68", "border": "#775439"}

_STAGES = ("seed", "sprout", "sapling", "tree")


def get_category_color(category):
    # One {background, border} pair per category: the pastel fill reads on
    # dark, the darker border carries the boundary on light. Mirrors
    # Flask's get_category_color() (values from --category-* in style.css).
    return _CATEGORY_COLORS.get(category, _FALLBACK_COLOR)


@st.cache_data(show_spinner=False)
def _growth_icon_uri(stage: str) -> str:
    """data: URI for a growth-stage SVG (no Flask /static to serve from)."""
    filename = {
        "seed": "seed.svg",
        "sprout": "sprout.svg",
        "sapling": "sapling.svg",
        "tree": "tree.svg",
    }.get(stage, "seed.svg")
    path = os.path.join(_ICON_DIR, filename)
    with open(path, "rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _connection_counts(note_ids):
    from app import db
    from app.models import Note, Relationship
    from sqlalchemy import func

    if not note_ids:
        return {}
    return dict(
        db.session.query(Note.id, func.count(Relationship.id))
        .outerjoin(
            Relationship,
            (Relationship.source_note_id == Note.id)
            | (Relationship.target_note_id == Note.id),
        )
        .filter(Note.id.in_(note_ids))
        .group_by(Note.id)
        .all()
    )


def _node_payload(note, rel_count, *, focus=False, level=0):
    from app.services.growth_service import compute_growth_stage

    color = get_category_color(note.category)
    stage = compute_growth_stage(note.created_at, rel_count)
    border = PINNED_BORDER_COLOR if note.is_pinned else color["border"]
    payload = {
        "id": note.id,
        "label": note.title[:30] + ("..." if len(note.title) > 30 else ""),
        "title": note.title,
        "category": note.category or "Uncategorized",
        "shape": "circularImage",
        "image": _growth_icon_uri(stage),
        "color": {"background": color["background"], "border": border},
        "borderWidth": 5 if note.is_pinned else 2,
        "size": 30 if focus else 20 + min(rel_count * 3, 30),
        "stage": stage,
        "is_pinned": note.is_pinned,
        "created_at": note.created_at.isoformat() if note.created_at else None,
    }
    if focus:
        payload["level"] = level
        payload["is_focus"] = False
    return payload


def _edge_payload(rel):
    return {
        "from": rel.source_note_id,
        "to": rel.target_note_id,
        "value": rel.similarity_score * 5,
        "title": f"{rel.relationship_type}: {rel.similarity_score:.0%}",
        # Deliberately no per-edge colour: a per-item colour would override
        # the global edges.color option entirely (same trap as the Flask app).
        "width": 1 + rel.similarity_score * 3,
        "similarity": rel.similarity_score,
        "type": rel.relationship_type,
    }


def list_categories(user_id: int) -> list[str]:
    """Distinct categories present in this user's visible notes."""
    from app import db
    from app.models import Note
    from sqlalchemy import distinct

    with app_context():
        rows = (
            db.session.query(distinct(Note.category))
            .filter_by(user_id=user_id, is_archived=False)
            .all()
        )
        return sorted({r[0] for r in rows if r and r[0]})


def note_choices(user_id: int) -> list[tuple[int, str]]:
    """(id, title) pairs for pickers — newest first."""
    from app.models import Note

    with app_context():
        notes = (
            Note.query.filter_by(user_id=user_id, is_archived=False)
            .order_by(Note.created_at.desc())
            .all()
        )
        return [(n.id, n.title) for n in notes]


def garden_payload(user_id: int, categories=None) -> dict:
    """Full-garden nodes/edges — port of /garden/data."""
    from app.models import Note, Relationship

    with app_context():
        query = Note.query.filter_by(user_id=user_id, is_archived=False)
        if categories:
            query = query.filter(Note.category.in_(categories))
        notes = query.all()

        # Both edge endpoints must be visible or vis-network gets an edge
        # with no node behind it (archived notes keep their rows).
        visible_ids = {n.id for n in notes}
        relationships = (
            Relationship.query.filter(
                Relationship.source_note_id.in_(visible_ids),
                Relationship.target_note_id.in_(visible_ids),
            ).all()
            if visible_ids
            else []
        )

        counts = _connection_counts([n.id for n in notes])
        nodes = []
        for note in notes:
            nodes.append(_node_payload(note, counts.get(note.id, 0)))
        edges = [_edge_payload(rel) for rel in relationships]
        return {"nodes": nodes, "edges": edges}


def focus_payload(
    user_id: int, note_id: int, *, depth: int = 2, min_similarity: float = 0.0
) -> dict:
    """Neighbourhood view — port of /garden/api/focus/<id> (level-by-level BFS)."""
    from app.models import Note, Relationship

    with app_context():
        note = Note.query.filter_by(id=note_id, user_id=user_id, is_archived=False).first()
        if note is None:
            return {"nodes": [], "edges": []}

        per_node_limit = 10
        node_payloads = {}
        notes_by_id = {note.id: note}
        edges = []
        seen_pairs = set()
        frontier_notes = {note.id: note}

        for level in range(depth):
            frontier_ids = list(frontier_notes.keys())
            if not frontier_ids:
                break

            rels = (
                Relationship.query.filter(
                    (
                        Relationship.source_note_id.in_(frontier_ids)
                        | Relationship.target_note_id.in_(frontier_ids)
                    )
                    & (Relationship.similarity_score >= min_similarity)
                )
                .order_by(Relationship.similarity_score.desc())
                .all()
            )

            by_anchor: dict[int, list] = {}
            for rel in rels:
                if rel.source_note_id in frontier_notes:
                    by_anchor.setdefault(rel.source_note_id, []).append(
                        (rel.target_note_id, rel)
                    )
                if rel.target_note_id in frontier_notes and rel.target_note_id != rel.source_note_id:
                    by_anchor.setdefault(rel.target_note_id, []).append(
                        (rel.source_note_id, rel)
                    )

            needed_ids = set()
            planned_edges = []
            for anchor_id, candidates in by_anchor.items():
                for other_id, rel in candidates[:per_node_limit]:
                    pair = tuple(sorted((anchor_id, other_id)))
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    planned_edges.append(rel)
                    if other_id not in notes_by_id:
                        needed_ids.add(other_id)

            new_notes_by_id = {}
            if needed_ids:
                new_notes = Note.query.filter(
                    Note.id.in_(needed_ids),
                    Note.user_id == user_id,
                    Note.is_archived == False,  # noqa: E712
                ).all()
                new_notes_by_id = {n.id: n for n in new_notes}
                notes_by_id.update(new_notes_by_id)

            for rel in planned_edges:
                if (
                    rel.source_note_id in notes_by_id
                    and rel.target_note_id in notes_by_id
                ):
                    edges.append(_edge_payload(rel))

            frontier_notes = new_notes_by_id

        counts = _connection_counts(list(notes_by_id.keys()))
        for nid, n in notes_by_id.items():
            payload = _node_payload(
                n, counts.get(nid, 0), focus=True, level=0
            )
            payload["size"] = 34 if nid == note.id else 22
            payload["is_focus"] = nid == note.id
            node_payloads[nid] = payload

        # Drop edges whose endpoints didn't survive (archived filtering).
        edges = [
            e for e in edges if e["from"] in node_payloads and e["to"] in node_payloads
        ]
        return {"nodes": list(node_payloads.values()), "edges": edges}


@st.cache_resource(show_spinner=False)
def _vis_js() -> str:
    with open(_VIS_PATH, "r", encoding="utf-8") as fh:
        return fh.read()


_GRAPH_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body, #mount { margin:0; padding:0; height:100%; width:100%;
    background: transparent; overflow: hidden; }
  #hint { position:absolute; left:8px; bottom:6px; font-size:11px;
    opacity:.65; pointer-events:none; }
</style>
</head>
<body>
<div id="mount"></div>
<div id="hint">Click a note to highlight its connections</div>
<script>{vis}</script>
<script>
const payload = {payload};
const nodes = new vis.DataSet(payload.nodes || []);
const edges = new vis.DataSet(payload.edges || []);
const options = {
  nodes: {
    shape: 'circularImage',
    borderWidth: 2,
    font: { size: 14, face: 'inherit', color: '#26332e' },
    shadow: { color: 'rgba(0,0,0,0.28)', size: 10, x: 0, y: 4 },
    chosen: false
  },
  edges: {
    color: { color: 'rgba(80,90,85,0.55)', highlight: '#193c32' },
    smooth: { type: 'continuous' },
    selectionWidth: 2
  },
  physics: {
    enabled: payload.physics !== false,
    stabilization: { iterations: 220, updateInterval: 25 },
    barnesHut: { gravitationalConstant: -3200, springLength: 130 }
  },
  interaction: { hover: true, tooltipDelay: 120, hideEdgesOnDrag: true }
};
const container = document.getElementById('mount');
const network = new vis.Network(container, {nodes, edges}, options);
network.once('stabilizationIterationsDone', function () {
  network.setOptions({physics: {enabled: payload.physics === true}});
  network.fit();
});

const baseColor = {};
nodes.forEach(n => { baseColor[n.id] = JSON.parse(JSON.stringify(n.color)); });
network.on('selectNode', function (params) {
  const keep = new Set(params.nodes);
  network.nodes().forEach(id => {
    const connected = keep.has(id) || network.getConnectedNodes(id).some(n => keep.has(n));
    if (!connected) {
      nodes.update({ id: id, color: {
        background: 'rgba(160,160,160,0.25)',
        border: 'rgba(160,160,160,0.25)' } });
    } else if (!keep.has(id)) {
      nodes.update({ id: id, color: baseColor[id] });
    }
  });
});
network.on('deselectNode', function () {
  nodes.forEach(n => nodes.update({ id: n.id, color: baseColor[n.id] }));
});
if (payload.search) {
  const q = payload.search.toLowerCase();
  const hits = nodes.get().filter(n => (n.title || n.label || '').toLowerCase().indexOf(q) !== -1);
  if (hits.length) {
    hits.forEach(n => nodes.update({ id: n.id, borderWidth: 6 }));
    network.fit(hits.map(n => n.id), {animation: true});
  }
}
</script>
</body>
</html>"""


def build_html(payload: dict, *, physics: bool = True, search: str = "") -> str:
    """Full graph document — split out so it can be tested without a browser."""
    data = dict(payload)
    data["physics"] = physics
    data["search"] = search
    # Escape "</" so a note title containing "</script>" cannot break out.
    blob = json.dumps(data).replace("</", "<\\/")
    # .replace(), not .format(): the JS is full of literal braces.
    return _GRAPH_TEMPLATE.replace("{vis}", _vis_js()).replace("{payload}", blob)


def render_graph(payload: dict, *, height: int = 560, physics: bool = True,
                 search: str = "") -> None:
    """Render the graph inline. Data + vendored vis-network, zero network I/O."""
    st.components.v1.html(build_html(payload, physics=physics, search=search),
                          height=height, scrolling=False)
