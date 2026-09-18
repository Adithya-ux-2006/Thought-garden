from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.search import bp
from app.models import Note, Tag, db
from app.forms import SearchForm
from app.services.search_service import hybrid_search
from sqlalchemy import or_


@bp.route('/', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    categories = db.session.query(Note.category).filter_by(user_id=current_user.id).distinct().all()
    form.category.choices = [('', 'All Categories')] + [(c[0], c[0]) for c in categories if c[0]]
    form.tag.choices = [('', 'All Tags')] + [(t.name, t.name) for t in 
        Tag.query.join(Note.tags).filter(Note.user_id == current_user.id).distinct().all()]
    
    results = []
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if query or request.args.get('category') or request.args.get('tag') or request.args.get('source_type'):
        category = request.args.get('category') or None
        tag = request.args.get('tag') or None
        source_type = request.args.get('source_type') or None
        
        results_pagination = hybrid_search(
            current_user.id, 
            query, 
            category=category, 
            tag=tag, 
            source_type=source_type,
            page=page, 
            per_page=per_page
        )
        results = results_pagination.items
        pagination = results_pagination
    else:
        pagination = None
    
    return render_template('search/search.html', form=form, results=results, 
                           pagination=pagination, query=query)


@bp.route('/api/suggest')
@login_required
def suggest():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    
    notes = Note.query.filter_by(user_id=current_user.id).filter(
        or_(Note.title.ilike(f'%{q}%'), Note.content.ilike(f'%{q}%'))
    ).limit(5).all()
    
    suggestions = [{'id': n.id, 'title': n.title, 'category': n.category} for n in notes]
    return jsonify(suggestions)