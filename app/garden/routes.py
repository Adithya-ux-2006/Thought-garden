from flask import render_template, jsonify, request, url_for
from flask_login import login_required, current_user
from app.garden import bp
from app.models import Note, Relationship, db
from app.services.growth_service import compute_growth_stage, growth_icon_filename
from app.services.similarity_service import explain_connection, relationship_label
from app.services.category_service import category_color, garden_category_metadata
from app.services.garden_service import collapse, load_plants_by_id
from sqlalchemy import func
from tg_ui import categories as tg_categories
from tg_ui.flowers import plant_filename
from tg_ui.presenters import flower_key

# Matches --pinned-color in tg_ui/static/css/tokens.css (also used by the
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


def _present_categories(user_id):
    """The categories actually growing in a user's garden (chips, legend),
    in palette order then custom ones, plus the most common category's
    flower to illustrate the growth path."""
    rows = db.session.query(Note.category, func.count(Note.id)).filter(
        Note.user_id == user_id, Note.is_archived == False  # noqa: E712
    ).group_by(Note.category).all()
    present = {}
    for category, count in rows:
        key = category or tg_categories.UNCATEGORIZED
        present[key] = present.get(key, 0) + count
    cats = [m for m in garden_category_metadata(sorted(present, key=str.casefold)) if m['value'] in present]
    common = max(present, key=present.get) if present else None
    return cats, tg_categories.flower(common) if common else 'wildflower'


@bp.route('/')
@login_required
def index():
    cats, growth_flower = _present_categories(current_user.id)
    return render_template('garden/index.html', categories=cats,
                           flowers=flower_key(c['value'] for c in cats), growth_flower=growth_flower)


def _visible_garden(user_id):
    """Active notes and the relationships between them - the shared basis
    of the graph and the list view.

    Both endpoints of every relationship must be visible, otherwise an
    archived note would leave a dangling edge. Leaf notes are still
    returned here; each consumer collapses them onto their plant.
    """
    notes = Note.query.filter_by(user_id=user_id, is_archived=False).all()
    visible_ids = {n.id for n in notes}
    relationships = Relationship.query.filter(
        Relationship.source_note_id.in_(visible_ids),
        Relationship.target_note_id.in_(visible_ids)
    ).all() if visible_ids else []

    return notes, relationships


@bp.route('/data')
@login_required
def data():
    notes, relationships = _visible_garden(current_user.id)
    visible, edges, counts, leaf_sets, owners, _, _ = collapse(notes, relationships)

    nodes = []
    for note in visible:
        color = category_color(note.category)
        rel_count = counts.get(note.id, 0)
        stage = compute_growth_stage(note.created_at, rel_count)
        # Every node is a growth-stage circularImage, so "pinned" reads
        # through a thicker gold ring; the fill stays category-colored.
        border = PINNED_BORDER_COLOR if note.is_pinned else color['border']
        leaf_count = len(leaf_sets.get(note.id, []))
        # The hover tooltip for a plant mentions its leaves.
        title = f'{note.title} ({leaf_count} leaves)' if leaf_count else note.title
        nodes.append({
            'id': note.id,
            'label': note.title[:30] + ('...' if len(note.title) > 30 else ''),
            'title': title,
            'category': note.category or 'Uncategorized',
            'shape': 'circularImage',
            'image': growth_icon_url(stage),
            # the note's flower at this stage, relative to /static
            'plant': plant_filename(note.category, stage),
            'flower': tg_categories.flower(note.category),
            'color': {'background': color['background'], 'border': border},
            'borderWidth': 5 if note.is_pinned else 2,
            'size': 20 + min(rel_count * 3, 30),
            'stage': stage,
            'is_pinned': note.is_pinned,
            'leaf_count': leaf_count,
            'created_at': note.created_at.isoformat() if note.created_at else None
        })
    
    edges_payload = []
    for rel in edges:
        edges_payload.append({
            'from': owners[rel.source_note_id],
            'to': owners[rel.target_note_id],
            'value': rel.similarity_score * 5,
            'title': f'{relationship_label(rel)}: {rel.similarity_score:.0%}',
            # No per-edge colour: it would override the theme-aware global
            # edges.color that main.js computes from CSS variables.
            'width': 1 + rel.similarity_score * 3,
            'similarity': rel.similarity_score,
            'type': rel.relationship_type,
            'method': rel.method
        })

    return jsonify({'nodes': nodes, 'edges': edges_payload})


@bp.route('/list')
@login_required
def list_view():
    """Text alternative to the canvas graph: every visible plant/note with
    its growth stage and each connection's reason, navigable by keyboard
    and screen reader. A plant's leaf notes are nested beneath it."""
    notes, relationships = _visible_garden(current_user.id)
    visible, edges, counts, leaf_sets, owners, _, _ = collapse(notes, relationships)

    by_id = {n.id: n for n in visible}
    all_by_id = {n.id: n for n in notes}
    leaf_by_id = {n.id: n for n in notes if n.parent_id}

    # "Why connected" is explained from the actual underlying notes (which
    # chunk pairs share keywords), while the row links to their plants.
    connections = {n.id: [] for n in visible}
    for rel in edges:
        source_top = owners[rel.source_note_id]
        target_top = owners[rel.target_note_id]
        src_note = all_by_id[rel.source_note_id]
        tgt_note = all_by_id[rel.target_note_id]
        connections[source_top].append((by_id[target_top], explain_connection(src_note, tgt_note, rel), rel))
        connections[target_top].append((by_id[source_top], explain_connection(tgt_note, src_note, rel), rel))

    entries = []
    for note in sorted(visible, key=lambda n: (not n.is_pinned, (n.category or '~').casefold(), n.title.casefold())):
        rel_count = counts.get(note.id, 0)
        stage = compute_growth_stage(note.created_at, rel_count)
        linked = sorted(connections[note.id], key=lambda item: item[2].similarity_score, reverse=True)
        leaves = sorted(
            (leaf_by_id[lid] for lid in leaf_sets.get(note.id, [])),
            key=lambda leaf: (leaf.part_index if leaf.part_index is not None else 0, leaf.id)
        )
        entries.append({
            'note': note,
            'stage': stage,
            'icon': growth_icon_url(stage),
            'plant': plant_filename(note.category, stage),
            'leaf_count': len(leaves),
            'leaves': leaves,
            'connections': [(other, why) for other, why, _ in linked],
        })

    leaf_total = sum(entry['leaf_count'] for entry in entries)
    return render_template('garden/list.html', entries=entries, edge_count=len(edges), leaf_total=leaf_total)


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
    emitted_rels = []
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
            emitted_rels.append(rel)
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

    # Collapse leaves onto their plants, same as /garden/data: the focus
    # view shows documents and standalone notes, never individual chunks.
    view_notes = list(notes_by_id.values())
    plant_of = load_plants_by_id(view_notes)
    visible, _, _, leaf_sets, _, edge_map, _ = collapse(view_notes, emitted_rels, plant_of)
    visible_by_id = {v.id: v for v in visible}

    # One aggregate query for the (small, bounded-by-depth) set of notes
    # that actually ended up in this view, rather than a query per node -
    # same reasoning as /garden/data. Growth stage uses each note's true
    # total connection count, matching /garden/data, not just how many
    # edges happened to survive this view's depth/similarity/per-node-limit
    # trimming.
    view_ids = list(visible_by_id.keys())
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

    node_payloads = {}
    for v in visible:
        payload = to_payload(v, 0 if v.id == note.id else 1)
        # If the focused note is a leaf, its plant is the focal node.
        is_focus = (v.id == note.id) or (note.id in leaf_sets.get(v.id, []))
        payload['is_focus'] = is_focus
        payload['size'] = 30 if is_focus else 20
        leaf_count = len(leaf_sets.get(v.id, []))
        payload['leaf_count'] = leaf_count
        if leaf_count:
            payload['title'] = f'{v.title} ({leaf_count} leaves)'
            payload['label'] = v.title[:30] + ('...' if len(v.title) > 30 else '')
        node_payloads[v.id] = payload

    edges = []
    for (source_top, target_top), rel in edge_map.items():
        edges.append({
            'from': source_top,
            'to': target_top,
            'value': rel.similarity_score * 5,
            'title': f'{relationship_label(rel)}: {rel.similarity_score:.0%}',
            'width': 1 + rel.similarity_score * 3,
            'similarity': rel.similarity_score,
            'type': rel.relationship_type,
            'method': rel.method
        })

    for nid, payload in node_payloads.items():
        n = visible_by_id[nid]
        stage = compute_growth_stage(n.created_at, connection_counts.get(nid, 0))
        border = PINNED_BORDER_COLOR if n.is_pinned else payload['color']['border']
        payload['shape'] = 'circularImage'
        payload['image'] = growth_icon_url(stage)
        payload['plant'] = plant_filename(n.category, stage)
        payload['stage'] = stage
        payload['is_pinned'] = n.is_pinned
        payload['color'] = {'background': payload['color']['background'], 'border': border}
        payload['borderWidth'] = 5 if n.is_pinned else 2

    return jsonify({'nodes': list(node_payloads.values()), 'edges': edges})


@bp.route('/note/<int:note_id>')
@login_required
def note_detail(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()

    # Show the focused note (and its leaves, if it's a plant) collapsed at
    # the plant level, so a plant with no edges of its own still lists the
    # documents its chunks connect to.
    scope = [note]
    if note.parent_id is None and note.leaf_notes:
        scope.extend(note.leaf_notes)
    scope_ids = {n.id for n in scope}

    rels = Relationship.query.filter(
        (Relationship.source_note_id.in_(scope_ids) |
         Relationship.target_note_id.in_(scope_ids)) &
        (Relationship.similarity_score >= 0.0)
    ).order_by(Relationship.similarity_score.desc()).limit(50).all() if scope_ids else []

    endpoint_ids = {r.source_note_id for r in rels} | {r.target_note_id for r in rels}
    endpoint_notes = Note.query.filter(
        Note.id.in_(endpoint_ids), Note.user_id == current_user.id, Note.is_archived == False
    ).all() if endpoint_ids else []

    supportive = scope + endpoint_notes
    plant_of = load_plants_by_id(supportive)
    visible, edges, _, _, owners, _, _ = collapse(supportive, rels, plant_of)

    by_id = {v.id: v for v in visible}
    supportive_by_id = {n.id: n for n in supportive}
    note_top_id = note.id if note.parent_id is None else note.parent_id

    connections = []
    seen = set()
    for rel in edges:
        a_top = owners[rel.source_note_id]
        b_top = owners[rel.target_note_id]
        other_top_id = b_top if a_top == note_top_id else (a_top if b_top == note_top_id else None)
        if other_top_id is None or other_top_id in seen:
            continue
        seen.add(other_top_id)
        other = by_id[other_top_id]
        src_note = supportive_by_id[rel.source_note_id]
        tgt_note = supportive_by_id[rel.target_note_id]
        why = explain_connection(src_note, tgt_note, rel)
        connections.append({
            'id': other.id,
            'title': other.title,
            'category': other.category,
            'similarity': rel.similarity_score,
            'type': rel.relationship_type,
            'label': why['label'],
            'method': why['method'],
            'shared_tags': why['shared_tags'],
            'shared_keywords': why['shared_keywords'],
            'reason': why['reason'],
            'preview': other.content[:150] + '...' if len(other.content) > 150 else other.content
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
