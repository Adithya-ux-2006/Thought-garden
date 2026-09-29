from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.notes import bp
from app.models import Note, Tag, Relationship, db
from app.forms import NoteForm
from app.services.note_lifecycle_service import (
    create_manual_note,
    import_notes_from_file,
    update_manual_note,
)
from app.services.knowledge_service import (
    duplicate_candidates,
    make_flashcards,
    summarize_note,
)


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
        title = (form.title.data or '').strip()
        try:
            result = create_manual_note(
                current_user.id,
                title=title,
                content=form.content.data,
                category=form.category.data,
                tags=form.tags.data,
                is_pinned=bool(form.is_pinned.data),
            )
        except Exception as error:
            flash(f'Note could not be saved: {error}', 'danger')
            return render_template('notes/create.html', form=form)

        if result.connection_error:
            flash(f'Note saved, but AI analysis failed: {result.connection_error}', 'warning')

        note = result.notes[0]
        flash('Note created successfully!', 'success')
        # Content-only input relies on the pipeline to invent a title and
        # category - land in the Garden so the user sees the finished note
        # in context rather than a half-enriched detail page.
        if not title:
            return redirect(url_for('garden.index'))
        return redirect(url_for('notes.view', note_id=note.id))

    return render_template('notes/create.html', form=form)


@bp.route('/<int:note_id>')
@login_required
def view(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    related = note.get_related_notes(limit=5, min_similarity=0.0)
    return render_template('notes/view.html', note=note, related=related)


@bp.route('/<int:note_id>/study')
@login_required
def study(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    summary = summarize_note(note)
    cards = make_flashcards(note)
    return render_template('notes/study.html', note=note, summary=summary, cards=cards)


@bp.route('/duplicates')
@login_required
def duplicates():
    candidates = duplicate_candidates(current_user.id)
    return render_template('notes/duplicates.html', duplicates=candidates)


@bp.route('/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    form = NoteForm(obj=note)
    form.tags.data = ', '.join([t.name for t in note.tags])

    if form.validate_on_submit():
        try:
            result = update_manual_note(
                note,
                title=form.title.data,
                content=form.content.data,
                category=form.category.data,
                tags=form.tags.data,
                is_pinned=bool(form.is_pinned.data),
            )
        except Exception as error:
            flash(f'Note could not be updated: {error}', 'danger')
            return render_template('notes/edit.html', form=form, note=note)

        if result.connection_error:
            flash(f'Note updated, but AI analysis failed: {result.connection_error}', 'warning')

        flash('Note updated successfully!', 'success')
        return redirect(url_for('notes.view', note_id=note.id))

    return render_template('notes/edit.html', form=form, note=note)


@bp.route('/<int:note_id>/delete', methods=['POST'])
@login_required
def delete(note_id):
    from app.services.embedding_service import invalidate_embedding_cache

    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    invalidate_embedding_cache(note_id)
    flash('Note deleted.', 'success')
    return redirect(url_for('notes.list_notes'))


@bp.route('/<int:note_id>/archive', methods=['POST'])
@login_required
def archive(note_id):
    from app.services.similarity_service import update_relationships_for_note

    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    note.is_archived = not note.is_archived

    if note.is_archived:
        # Archiving used to just flip the flag and leave relationship rows
        # in place, so the garden graph kept returning edges pointing at a
        # node that was no longer there. Drop them here instead of relying
        # on every reader to filter them out.
        Relationship.query.filter(
            (Relationship.source_note_id == note.id) | (Relationship.target_note_id == note.id)
        ).delete(synchronize_session=False)
        db.session.commit()
    else:
        db.session.commit()
        try:
            update_relationships_for_note(note)
        except Exception as e:
            flash(f'Note unarchived, but AI analysis failed: {str(e)}', 'warning')

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

    category = request.form.get('category') or None
    try:
        notes = import_notes_from_file(current_user.id, file, category=category)
    except ValueError as error:
        flash(str(error), 'danger')
        return redirect(url_for('notes.create'))
    except Exception as error:
        flash(f'Error importing document: {error}', 'danger')
        return redirect(url_for('notes.create'))

    flash(f'Successfully imported {len(notes.notes)} note(s) from {file.filename}', 'success')
    if len(notes.notes) == 1:
        return redirect(url_for('notes.view', note_id=notes.notes[0].id))
    return redirect(url_for('notes.list_notes'))


@bp.route('/archived')
@login_required
def archived():
    return redirect(url_for('notes.list_notes', archived=1))
