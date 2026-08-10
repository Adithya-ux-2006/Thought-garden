from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.main import bp
from app.models import Note, Tag, Relationship, db, note_tags
from sqlalchemy import func, or_


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_notes': Note.query.filter_by(user_id=current_user.id).count(),
        'documents': Note.query.filter_by(user_id=current_user.id).filter(Note.source_type != 'manual').count(),
        'connections': Relationship.query.join(Note, Relationship.source_note_id == Note.id).filter(Note.user_id == current_user.id).count(),
        'tags': Tag.query.join(note_tags).join(Note).filter(Note.user_id == current_user.id).distinct().count(),
        'pinned': Note.query.filter_by(user_id=current_user.id, is_pinned=True).count(),
    }
    
    recent_notes = Note.query.filter_by(user_id=current_user.id, is_archived=False).order_by(Note.created_at.desc()).limit(5).all()
    recent_updated = Note.query.filter_by(user_id=current_user.id, is_archived=False).order_by(Note.updated_at.desc()).limit(5).all()
    
    most_connected = db.session.query(Note, func.count(Relationship.id).label('conn_count'))\
        .join(Relationship, (Relationship.source_note_id == Note.id) | (Relationship.target_note_id == Note.id))\
        .filter(Note.user_id == current_user.id)\
        .group_by(Note.id)\
        .order_by(func.count(Relationship.id).desc())\
        .limit(5).all()
    
    categories = db.session.query(Note.category, func.count(Note.id))\
        .filter(Note.user_id == current_user.id, Note.category.isnot(None))\
        .group_by(Note.category)\
        .order_by(func.count(Note.id).desc())\
        .all()
    
    recent_connections = Relationship.query.join(Note, Relationship.source_note_id == Note.id)\
        .filter(Note.user_id == current_user.id)\
        .order_by(Relationship.created_at.desc())\
        .limit(5).all()
    
    orphan_notes = Note.query.filter_by(user_id=current_user.id, is_archived=False)\
        .filter(~Note.relationships.any(), ~Note.inverse_relationships.any())\
        .limit(5).all()
    
    rediscover = Note.query.filter_by(user_id=current_user.id, is_archived=False)\
        .order_by(Note.created_at.asc())\
        .limit(3).all()
    
    return render_template('main/dashboard.html',
                           stats=stats,
                           recent_notes=recent_notes,
                           recent_updated=recent_updated,
                           most_connected=most_connected,
                           categories=categories,
                           recent_connections=recent_connections,
                           orphan_notes=orphan_notes,
                           rediscover=rediscover)


@bp.route('/insights')
@login_required
def insights():
    total_notes = Note.query.filter_by(user_id=current_user.id).count()
    
    if total_notes == 0:
        return render_template('main/insights.html', insights={})
    
    most_connected_topic = db.session.query(Note.category, func.count(Relationship.id))\
        .join(Relationship, (Relationship.source_note_id == Note.id) | (Relationship.target_note_id == Note.id))\
        .filter(Note.user_id == current_user.id, Note.category.isnot(None))\
        .group_by(Note.category)\
        .order_by(func.count(Relationship.id).desc())\
        .first()
    
    largest_category = db.session.query(Note.category, func.count(Note.id))\
        .filter(Note.user_id == current_user.id, Note.category.isnot(None))\
        .group_by(Note.category)\
        .order_by(func.count(Note.id).desc())\
        .first()
    
    strongest_connection = Relationship.query.join(Note, Relationship.source_note_id == Note.id)\
        .filter(Note.user_id == current_user.id)\
        .order_by(Relationship.similarity_score.desc())\
        .first()
    
    notes_no_connections = Note.query.filter_by(user_id=current_user.id, is_archived=False)\
        .filter(~Note.relationships.any(), ~Note.inverse_relationships.any())\
        .count()
    
    recently_growing = db.session.query(Note.category, func.count(Note.id))\
        .filter(Note.user_id == current_user.id, Note.category.isnot(None),
                Note.created_at >= func.date('now', '-30 days'))\
        .group_by(Note.category)\
        .order_by(func.count(Note.id).desc())\
        .first()
    
    insights = {
        'most_connected_topic': most_connected_topic,
        'largest_category': largest_category,
        'strongest_connection': strongest_connection,
        'notes_no_connections': notes_no_connections,
        'recently_growing': recently_growing,
        'total_notes': total_notes,
    }
    
    return render_template('main/insights.html', insights=insights)