from collections import Counter

from flask import render_template, jsonify, request, url_for
from flask_login import login_required, current_user
from app.garden import bp
from app.models import Note, Relationship, db
from app.services.growth_service import (
    compute_growth_stage,
    growth_icon_filename,
    was_recently_watered,
)


def growth_icon_url(stage):
    return url_for('static', filename=f'img/garden/{growth_icon_filename(stage)}')


def build_note_node(note, connection_count, extra=None):
    """Shared node-dict builder so the main garden view and the focus
    view render notes the same way: a growth-stage icon with a
    category-colored ring around it."""
    stage = compute_growth_stage(note.created_at, connection_count)
    color = get_category_color(note.category)

    node = {
        'id': note.id,
        'label': note.title[:30] + ('...' if len(note.title) > 30 else ''),
        'title': note.title,
        'category': note.category or 'Uncategorized',
        'shape': 'circularImage',
        'image': growth_icon_url(stage),
        'color': {'border': color, 'background': color},
        'stage': stage,
        'watered': was_recently_watered(note.updated_at),
        'is_pinned': note.is_pinned,
        'created_at': note.created_at.isoformat() if note.created_at else None,
    }
    if extra:
        node.update(extra)
    return node


@bp.route('/')
@login_required
def index():
    notes = Note.query.filter_by(user_id=current_user.id, is_archived=False).all()
    categories = list(set(n.category for n in notes if n.category))
    return render_template('garden/index.html', categories=categories)


@bp.route('/data')
@login_required
def data():
    notes = Note.query.filter_by(user_id=current_user.id, is_archived=False).all()
    relationships = Relationship.query.join(Note, Relationship.source_note_id == Note.id)\
        .filter(Note.user_id == current_user.id).all()
    
    # Count each note's connections from the relationships already fetched
    # above instead of running a fresh query per note.
    connection_counts = Counter()
    for rel in relationships:
        connection_counts[rel.source_note_id] += 1
        connection_counts[rel.target_note_id] += 1

    nodes = []
    for note in notes:
        connection_count = connection_counts.get(note.id, 0)
        nodes.append(build_note_node(note, connection_count, extra={
            'size': 20 + min(connection_count * 3, 30),
        }))
    
    edges = []
    for rel in relationships:
        edges.append({
            'from': rel.source_note_id,
            'to': rel.target_note_id,
            'value': rel.similarity_score * 5,
            'title': f'{rel.relationship_type}: {rel.similarity_score:.0%}',
            'color': {'color': '#999', 'highlight': '#666', 'hover': '#333'},
            'width': 1 + rel.similarity_score * 3,
            'similarity': rel.similarity_score,
            'type': rel.relationship_type
        })
    
    return jsonify({'nodes': nodes, 'edges': edges})


@bp.route('/focus/<int:note_id>')
@login_required
def focus(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    depth = request.args.get('depth', 2, type=int)
    min_similarity = request.args.get('min_similarity', 0.0, type=float)
    
    visited = set()
    nodes = []
    edges = []
    
    def add_node(n, level=0):
        if n.id in visited or level > depth:
            return
        visited.add(n.id)
        connection_count = len(n.get_all_relationships())
        nodes.append(build_note_node(n, connection_count, extra={
            'size': 30 if n.id == note_id else 20,
            'level': level,
            'is_focus': n.id == note_id,
        }))
        
        related = n.get_related_notes(limit=10, min_similarity=min_similarity)
        for related_note, sim, rel_type in related:
            if related_note.id not in visited or level < depth:
                edges.append({
                    'from': n.id,
                    'to': related_note.id,
                    'value': sim * 5,
                    'title': f'{rel_type}: {sim:.0%}',
                    'color': {'color': '#999', 'highlight': '#666', 'hover': '#333'},
                    'width': 1 + sim * 3,
                    'similarity': sim,
                    'type': rel_type
                })
                add_node(related_note, level + 1)
    
    add_node(note)
    
    return jsonify({'nodes': nodes, 'edges': edges})


@bp.route('/note/<int:note_id>')
@login_required
def note_detail(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    related = note.get_related_notes(limit=10, min_similarity=0.0)
    
    connections = []
    for related_note, sim, rel_type in related:
        connections.append({
            'id': related_note.id,
            'title': related_note.title,
            'category': related_note.category,
            'similarity': sim,
            'type': rel_type,
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


def get_category_color(category):
    colors = {
        'AI': '#6366f1',
        'Artificial Intelligence': '#6366f1',
        'Cybersecurity': '#ef4444',
        'Software Engineering': '#10b981',
        'Operating Systems': '#f59e0b',
        'Research': '#8b5cf6',
        'Ideas': '#ec4899',
        'Study': '#06b6d4',
        'Study Material': '#06b6d4',
    }
    return colors.get(category, '#64748b')
