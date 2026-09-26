from flask import render_template, jsonify, request, url_for
from flask_login import login_required, current_user
from app.garden import bp
from app.models import Note, Relationship, db
from app.services.growth_service import compute_growth_stage, growth_icon_filename
from app.services.similarity_service import explain_connection, relationship_label
from app.services.category_service import category_color, garden_category_metadata
from sqlalchemy import func

# Matches --pinned-color in app/static/css/style.css (also used by the
# garden legend's pinned swatch, so the two stay in sync) - CSS can't be
# read from here, so it's mirrored by hand, same as category_service.category_color().
# It's a darkened (0.9x) derivative of --warning-color: the raw token was
# only 2.94:1 against the light theme's cream ground as a ring color, just
# under the 3:1 bar. Reused rather than inventing a new hex, same reasoning
# as every category border: the server can't know the client's theme, so
# this one value has to hold up on both a cream and a near-black canvas
# (verified 3.58:1 light / 4.35:1 dark).
PINNED_BORDER_COLOR = '#a57834'


def growth_icon_url(stage):
    return url_for('static', filename=f'img/garden/{growth_icon_filename(stage)}')


@bp.route('/')
@login_required
def index():
    return render_template('garden/index.html', categories=garden_category_metadata())


def _visible_garden(user_id):
    """Active notes, the relationships between them, and each note's
    relationship count - the shared basis of the graph and the list view.

    Both endpoints of every relationship must be visible, otherwise an
    archived note would leave a dangling edge.
    """
    notes = Note.query.filter_by(user_id=user_id, is_archived=False).all()
    visible_ids = {n.id for n in notes}
    relationships = Relationship.query.filter(
        Relationship.source_note_id.in_(visible_ids),
        Relationship.target_note_id.in_(visible_ids)
    ).all() if visible_ids else []

    relationship_counts = dict(
        db.session.query(
            Note.id,
            func.count(Relationship.id)
        )
        .outerjoin(
            Relationship,
            (Relationship.source_note_id == Note.id) | (Relationship.target_note_id == Note.id)
        )
        .filter(Note.id.in_(visible_ids))
        .group_by(Note.id)
        .all()
    ) if visible_ids else {}

    return notes, relationships, relationship_counts


@bp.route('/data')
@login_required
def data():
    notes, relationships, relationship_counts = _visible_garden(current_user.id)

    nodes = []
    for note in notes:
        color = category_color(note.category)
        rel_count = relationship_counts.get(note.id, 0)
        stage = compute_growth_stage(note.created_at, rel_count)
        # Every node is a growth-stage circularImage, so "pinned" reads
        # through a thicker gold ring; the fill stays category-colored.
        border = PINNED_BORDER_COLOR if note.is_pinned else color['border']
        nodes.append({
            'id': note.id,
            'label': note.title[:30] + ('...' if len(note.title) > 30 else ''),
            'title': note.title,
            'category': note.category or 'Uncategorized',
            'shape': 'circularImage',
            'image': growth_icon_url(stage),
            'color': {'background': color['background'], 'border': border},
            'borderWidth': 5 if note.is_pinned else 2,
            'size': 20 + min(rel_count * 3, 30),
            'stage': stage,
            'is_pinned': note.is_pinned,
            'created_at': note.created_at.isoformat() if note.created_at else None
        })
    
    edges = []
    for rel in relationships:
        edges.append({
            'from': rel.source_note_id,
            'to': rel.target_note_id,
            'value': rel.similarity_score * 5,
            'title': f'{relationship_label(rel)}: {rel.similarity_score:.0%}',
            # No per-edge colour: it would override the theme-aware global
            # edges.color that main.js computes from CSS variables.
            'width': 1 + rel.similarity_score * 3,
            'similarity': rel.similarity_score,
            'type': rel.relationship_type,
            'method': rel.method
        })

    return jsonify({'nodes': nodes, 'edges': edges})


@bp.route('/list')
@login_required
def list_view():
    """Text alternative to the canvas graph: every visible note with its
    growth stage and each connection's reason, navigable by keyboard and
    screen reader."""
    notes, relationships, relationship_counts = _visible_garden(current_user.id)
    by_id = {n.id: n for n in notes}

    connections = {n.id: [] for n in notes}
    for rel in relationships:
        source, target = by_id[rel.source_note_id], by_id[rel.target_note_id]
        connections[source.id].append((target, explain_connection(source, target, rel), rel))
        connections[target.id].append((source, explain_connection(target, source, rel), rel))

    entries = []
    for note in sorted(notes, key=lambda n: (not n.is_pinned, (n.category or '~').casefold(), n.title.casefold())):
        rel_count = relationship_counts.get(note.id, 0)
        stage = compute_growth_stage(note.created_at, rel_count)
        linked = sorted(connections[note.id], key=lambda item: item[2].similarity_score, reverse=True)
        entries.append({
            'note': note,
            'stage': stage,
            'icon': growth_icon_url(stage),
            'connections': [(other, why) for other, why, _ in linked],
        })

    return render_template('garden/list.html', entries=entries, edge_count=len(relationships))


@bp.route('/focus/<int:note_id>')
@login_required
def focus(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    return render_template('garden/focus.html', note=note)


@bp.route('/api/focus/<int:note_id>')
@login_required
def focus_data(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    depth = request.args.get('depth', 2, type=int)
    min_similarity = request.args.get('min_similarity', 0.0, type=float)
    per_node_limit = 10

    def to_payload(n, level):
        return {
            'id': n.id,
            'label': n.title[:30] + ('...' if len(n.title) > 30 else ''),
            'title': n.title,
            'category': n.category or 'Uncategorized',
            'color': category_color(n.category),
            'size': 30 if n.id == note_id else 20,
            'level': level,
            'is_focus': n.id == note_id
        }

    node_payloads = {note.id: to_payload(note, 0)}
    edges = []
    seen_pairs = set()
    frontier_notes = {note.id: note}
    # Growth stage needs each note's total connection count and created_at,
    # neither of which survives once to_payload() has turned a Note into a
    # plain dict - kept alongside node_payloads so the patch pass below has
    # the actual objects to work with.
    notes_by_id = {note.id: note}

    for level in range(depth):
        frontier_ids = list(frontier_notes.keys())
        if not frontier_ids:
            break

        # One query per BFS level for every relationship touching the frontier.
        rels = Relationship.query.filter(
            ((Relationship.source_note_id.in_(frontier_ids)) |
             (Relationship.target_note_id.in_(frontier_ids))) &
            (Relationship.similarity_score >= min_similarity)
        ).order_by(Relationship.similarity_score.desc()).all()

        by_anchor = {}
        for rel in rels:
            if rel.source_note_id in frontier_notes:
                by_anchor.setdefault(rel.source_note_id, []).append((rel.target_note_id, rel))
            if rel.target_note_id in frontier_notes and rel.target_note_id != rel.source_note_id:
                by_anchor.setdefault(rel.target_note_id, []).append((rel.source_note_id, rel))

        needed_ids = set()
        planned_edges = []
        for anchor_id, candidates in by_anchor.items():
            # rels came back ordered by similarity desc, so the first
            # per_node_limit entries per anchor are its strongest links.
            for other_id, rel in candidates[:per_node_limit]:
                # A-B and B-A are the same relationship row seen from both
                # ends; without this the same edge got appended twice and
                # drawn as overlapping lines.
                pair = tuple(sorted((anchor_id, other_id)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                planned_edges.append(rel)
                if other_id not in node_payloads:
                    needed_ids.add(other_id)

        new_notes_by_id = {}
        if needed_ids:
            # Archived notes keep their relationship rows too (same root
            # cause as /garden/data), so this has to exclude them - not
            # just filter by ownership - or an archived note becomes an
            # edge endpoint with no node behind it.
            new_notes = Note.query.filter(
                Note.id.in_(needed_ids), Note.user_id == current_user.id, Note.is_archived == False
            ).all()
            new_notes_by_id = {n.id: n for n in new_notes}
            for other_id, n in new_notes_by_id.items():
                node_payloads[other_id] = to_payload(n, level + 1)
            notes_by_id.update(new_notes_by_id)

        for rel in planned_edges:
            # Only emit an edge once both endpoints actually became nodes -
            # an other_id that turned out archived (filtered out above)
            # never got a payload, so its edge must be dropped too.
            if rel.source_note_id not in node_payloads or rel.target_note_id not in node_payloads:
                continue
            edges.append({
                'from': rel.source_note_id,
                'to': rel.target_note_id,
                'value': rel.similarity_score * 5,
                'title': f'{relationship_label(rel)}: {rel.similarity_score:.0%}',
                # Same reasoning as /garden/data: no per-edge colour, so
                # the themed global edges.color option actually applies.
                'width': 1 + rel.similarity_score * 3,
                'similarity': rel.similarity_score,
                'type': rel.relationship_type,
                'method': rel.method
            })

        frontier_notes = new_notes_by_id

    # One aggregate query for the (small, bounded-by-depth) set of notes
    # that actually ended up in this view, rather than a query per node -
    # same reasoning as /garden/data's relationship_counts. Growth stage
    # here uses each note's true total connection count, matching how
    # /garden/data computes it, not just how many edges happened to survive
    # this view's depth/similarity/per-node-limit trimming.
    view_ids = list(node_payloads.keys())
    connection_counts = dict(
        db.session.query(
            Note.id,
            func.count(Relationship.id)
        )
        .outerjoin(
            Relationship,
            (Relationship.source_note_id == Note.id) | (Relationship.target_note_id == Note.id)
        )
        .filter(Note.id.in_(view_ids))
        .group_by(Note.id)
        .all()
    ) if view_ids else {}

    for nid, payload in node_payloads.items():
        n = notes_by_id[nid]
        stage = compute_growth_stage(n.created_at, connection_counts.get(nid, 0))
        border = PINNED_BORDER_COLOR if n.is_pinned else payload['color']['border']
        payload['shape'] = 'circularImage'
        payload['image'] = growth_icon_url(stage)
        payload['stage'] = stage
        payload['is_pinned'] = n.is_pinned
        payload['color'] = {'background': payload['color']['background'], 'border': border}
        payload['borderWidth'] = 5 if n.is_pinned else 2

    return jsonify({'nodes': list(node_payloads.values()), 'edges': edges})


@bp.route('/note/<int:note_id>')
@login_required
def note_detail(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    related = note.get_related_notes(limit=10, min_similarity=0.0)
    
    connections = []
    for related_note, rel in related:
        why = explain_connection(note, related_note, rel)
        connections.append({
            'id': related_note.id,
            'title': related_note.title,
            'category': related_note.category,
            'similarity': rel.similarity_score,
            'type': rel.relationship_type,
            'label': why['label'],
            'method': why['method'],
            'shared_tags': why['shared_tags'],
            'shared_keywords': why['shared_keywords'],
            'reason': why['reason'],
            'preview': related_note.content[:150] + '...' if len(related_note.content) > 150 else related_note.content
        })
    
    return jsonify({
        'id': note.id,
        'title': note.title,
        'content': note.content,
        'category': note.category,
        'tags': [t.name for t in note.tags],
        'created_at': note.created_at.isoformat() if note.created_at else None,
        'updated_at': note.updated_at.isoformat() if note.updated_at else None,
        'connections': connections
    })
