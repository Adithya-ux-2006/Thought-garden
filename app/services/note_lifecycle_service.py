"""Sequential application workflow for creating, importing, and connecting notes."""

from dataclasses import dataclass

from app import db
from app.models import Note, Tag
from app.services.document_service import (
    chunk_text,
    extract_text,
    generate_title_from_content,
    validate_file,
)
from app.services.semantic_pipeline_service import generate_note_title, queue_semantic_pipeline


@dataclass
class NoteLifecycleResult:
    notes: list[Note]
    connection_error: str | None = None
    job_ids: list[int] | None = None


def parse_tag_names(value: str | None) -> list[str]:
    """Normalize a comma-separated tag field without creating duplicates."""
    if not value:
        return []
    return list(dict.fromkeys(tag.strip() for tag in value.split(',') if tag.strip()))


def get_or_create_tags(tag_names: list[str]) -> list[Tag]:
    tags = []
    for name in tag_names:
        tag = Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags


def _synchronize_connections(notes: list[Note]) -> tuple[str | None, list[int]]:
    """Start automatic metadata, semantic, and relationship work after persistence."""
    try:
        jobs = queue_semantic_pipeline(notes)
        return None, [job.id for job in jobs]
    except Exception as error:
        db.session.rollback()
        return str(error), []


def create_note_batch(user_id, note_data, *, source_type='manual'):
    """Persist a prepared group of notes, then discover their connections once."""
    notes = []
    for item in note_data:
        note = Note(
            user_id=user_id,
            title=item.get('title') or generate_note_title(item['content']),
            content=item['content'],
            category=item.get('category') or None,
            source_type=item.get('source_type', source_type),
            source_filename=item.get('source_filename'),
            is_pinned=item.get('is_pinned', False),
        )
        tag_names = item.get('tags', [])
        if isinstance(tag_names, str):
            tag_names = parse_tag_names(tag_names)
        note.tags = get_or_create_tags(tag_names)
        db.session.add(note)
        notes.append(note)

    db.session.commit()
    error, job_ids = _synchronize_connections(notes)
    return NoteLifecycleResult(notes, error, job_ids)


def create_manual_note(user_id, *, title, content, category=None, tags=None, is_pinned=False):
    note = Note(
        user_id=user_id,
        title=(title or '').strip() or generate_note_title(content),
        content=content,
        category=category or None,
        source_type='manual',
        is_pinned=is_pinned,
    )
    note.tags = get_or_create_tags(parse_tag_names(tags))
    db.session.add(note)
    db.session.commit()
    error, job_ids = _synchronize_connections([note])
    return NoteLifecycleResult([note], error, job_ids)


def update_manual_note(note, *, title, content, category=None, tags=None, is_pinned=False):
    note.title = (title or '').strip() or generate_note_title(content)
    note.content = content
    note.category = category or None
    note.is_pinned = is_pinned
    note.tags = get_or_create_tags(parse_tag_names(tags))
    db.session.commit()
    error, job_ids = _synchronize_connections([note])
    return NoteLifecycleResult([note], error, job_ids)


def import_notes_from_file(user_id, file, *, category=None):
    is_valid, error = validate_file(file)
    if not is_valid:
        raise ValueError(error)

    content = extract_text(file, file.filename)
    if not content.strip():
        raise ValueError('Could not extract text from file.')

    chunks = chunk_text(content)
    source_type = file.filename.rsplit('.', 1)[1].lower()
    base_title = generate_title_from_content(content, file.filename)
    note_data = []
    for index, chunk in enumerate(chunks, 1):
        title = f'{base_title} (Part {index})' if len(chunks) > 1 else base_title
        note_data.append({
            'title': title,
            'content': chunk,
            'category': category,
            'source_type': source_type,
            'source_filename': file.filename,
        })
    return create_note_batch(user_id, note_data)
