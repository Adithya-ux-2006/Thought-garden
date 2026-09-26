from flask import render_template, redirect, url_for, flash, request, abort, current_app, g, jsonify
from flask_login import login_required, current_user
from app.notes import bp
from app.models import Note, Tag, Relationship, db
from app.forms import NoteForm
from app.services.keyword_service import extract_keywords, suggest_tags
from app.services.similarity_service import explain_connection, rebuild_user_graph
from app.services.tag_service import get_or_create_tags, prune_orphan_tags
from app.services import indexer


def _report_failure(message, category='warning'):
    """Log the active exception in full; show the user only a generic message
    plus a reference that matches the request ID in the logs."""
    current_app.logger.exception(message)
    flash(f"{message} (Reference: {g.get('request_id', '-')})", category)


def parse_tags(tag_string):
    if not tag_string:
        return []
    tags = [t.strip() for t in tag_string.split(',') if t.strip()]
    return tags


@bp.route('/')
@login_required
def list_notes():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    query = Note.query.filter_by(user_id=current_user.id)
    
    if request.args.get('archived'):
        query = query.filter_by(is_archived=True)
    else:
        query = query.filter_by(is_archived=False)
    
    if request.args.get('pinned'):
        query = query.filter_by(is_pinned=True)
    
    category = request.args.get('category')
    if category:
        query = query.filter_by(category=category)
    
    tag = request.args.get('tag')
    if tag:
        query = query.join(Note.tags).filter(Tag.name == tag)
    
    notes = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).paginate(page=page, per_page=per_page)
    
    categories = db.session.query(Note.category).filter_by(user_id=current_user.id).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    tags = Tag.query.join(Note.tags).filter(Note.user_id == current_user.id).distinct().all()
    
    return render_template('notes/list.html', notes=notes, categories=categories, tags=tags)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(
            user_id=current_user.id,
            title=form.title.data,
            content=form.content.data,
            category=form.category.data or None,
            source_type='manual'
        )
        db.session.add(note)
        db.session.flush()
        
        tag_names = parse_tags(form.tags.data)
        if tag_names:
            note.tags = get_or_create_tags(current_user.id, tag_names)

        db.session.commit()

        try:
            rebuild_user_graph(current_user.id)
        except Exception:
            _report_failure('Note saved, but finding connections failed.')

        # Fast keyword-tier relationships are already in place above. This
        # just queues the note for the background worker's embedding pass,
        # which will upgrade them to embedding-tier once it gets to it.
        indexer.enqueue(note)

        flash('Note created successfully!', 'success')
        return redirect(url_for('notes.view', note_id=note.id))

    return render_template('notes/create.html', form=form)


@bp.route('/<int:note_id>')
@login_required
def view(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    related = [(other, explain_connection(note, other, rel))
               for other, rel in note.get_related_notes(limit=5, min_similarity=0.0)]
    return render_template('notes/view.html', note=note, related=related)


@bp.route('/api/suggest-tags', methods=['POST'])
@login_required
def suggest_tags_api():
    data = request.get_json(silent=True) or {}
    title = data.get('title') if isinstance(data.get('title'), str) else ''
    content = data.get('content') if isinstance(data.get('content'), str) else ''
    current = parse_tags(data.get('tags') if isinstance(data.get('tags'), str) else '')

    related = []
    note_id = data.get('note_id')
    if isinstance(note_id, int) and not isinstance(note_id, bool):
        note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
        if note:
            related = [other for other, _ in note.get_related_notes(limit=5)]

    user_tags = [t.name for t in Tag.query.filter_by(user_id=current_user.id).order_by(Tag.name)]
    return jsonify({'suggestions': suggest_tags(title, content, current, user_tags, related)})


@bp.route('/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    form = NoteForm(obj=note)
    if request.method == 'GET':
        form.tags.data = ', '.join([t.name for t in note.tags])
        # Purely cosmetic: without its value present in `choices`, WTForms'
        # select widget can't mark any <option> as selected, so a note
        # saved under a category outside the presets would render with
        # nothing selected. validate_choice=False (see NoteForm) already
        # makes POST accept any category regardless of this list - this
        # only affects what shows pre-selected on the GET-rendered form.
        if note.category and note.category not in dict(form.category.choices):
            form.category.choices.append((note.category, note.category))

    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data
        note.category = form.category.data or None
        note.is_pinned = form.is_pinned.data

        tag_names = parse_tags(form.tags.data)
        note.tags = get_or_create_tags(current_user.id, tag_names)
        prune_orphan_tags(current_user.id)

        db.session.commit()

        try:
            rebuild_user_graph(current_user.id)
        except Exception:
            _report_failure('Note updated, but finding connections failed.')

        indexer.enqueue(note)

        flash('Note updated successfully!', 'success')
        return redirect(url_for('notes.view', note_id=note.id))

    return render_template('notes/edit.html', form=form, note=note)


@bp.route('/<int:note_id>/delete', methods=['POST'])
@login_required
def delete(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    db.session.delete(note)
    db.session.flush()
    prune_orphan_tags(current_user.id)
    db.session.commit()
    flash('Note deleted.', 'success')
    return redirect(url_for('notes.list_notes'))


@bp.route('/<int:note_id>/archive', methods=['POST'])
@login_required
def archive(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    note.is_archived = not note.is_archived

    if note.is_archived:
        # Drop edges here rather than relying on every reader to filter out
        # archived endpoints.
        Relationship.query.filter(
            (Relationship.source_note_id == note.id) | (Relationship.target_note_id == note.id)
        ).delete(synchronize_session=False)
        db.session.commit()
    else:
        db.session.commit()
        try:
            rebuild_user_graph(current_user.id)
        except Exception:
            _report_failure('Note unarchived, but finding connections failed.')

    flash(f'Note {"archived" if note.is_archived else "unarchived"}.', 'success')
    return redirect(url_for('notes.view', note_id=note.id))


@bp.route('/<int:note_id>/pin', methods=['POST'])
@login_required
def pin(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    note.is_pinned = not note.is_pinned
    db.session.commit()
    flash(f'Note {"pinned" if note.is_pinned else "unpinned"}.', 'success')
    return redirect(url_for('notes.view', note_id=note.id))


@bp.route('/import', methods=['POST'])
@login_required
def import_document():
    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('notes.create'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('notes.create'))
    
    from app.services.document_service import validate_file, extract_text, create_notes_from_document
    
    is_valid, error = validate_file(file)
    if not is_valid:
        flash(error, 'danger')
        return redirect(url_for('notes.create'))
    
    try:
        content = extract_text(file, file.filename)
        if not content.strip():
            flash('Could not extract text from file.', 'danger')
            return redirect(url_for('notes.create'))
        
        category = request.form.get('category')
        notes = create_notes_from_document(current_user.id, content, file.filename, category)
        
        flash(f'Successfully imported {len(notes)} note(s) from {file.filename}', 'success')
        if len(notes) == 1:
            return redirect(url_for('notes.view', note_id=notes[0].id))
        return redirect(url_for('notes.list_notes'))
    except Exception:
        _report_failure('Could not import this document. Please check the file and try again.', 'danger')
        return redirect(url_for('notes.create'))


@bp.route('/archived')
@login_required
def archived():
    return redirect(url_for('notes.list_notes', archived=1))
