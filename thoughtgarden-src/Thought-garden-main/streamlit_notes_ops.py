"""Notes page data operations — Streamlit-side wrappers around Flask models/services.

All DB work runs under streamlit_db.app_context(). Business logic stays in
app/services/* (unchanged).
"""

from __future__ import annotations

import io
from typing import Any

from streamlit_db import app_context

# Mirrors app.forms.NoteForm.category choices (value, label).
CATEGORY_CHOICES = [
    ("", "Select Category"),
    ("AI", "Artificial Intelligence"),
    ("Cybersecurity", "Cybersecurity"),
    ("Software Engineering", "Software Engineering"),
    ("Operating Systems", "Operating Systems"),
    ("Research", "Research"),
    ("Ideas", "Ideas"),
    ("Study", "Study Material"),
    ("Other", "Other"),
]

CATEGORY_LABELS = {value: label for value, label in CATEGORY_CHOICES}
CATEGORY_OPTIONS = [value for value, _ in CATEGORY_CHOICES]


def _parse_tags(tag_string: str | None) -> list[str]:
    if not tag_string:
        return []
    return [t.strip() for t in tag_string.split(",") if t.strip()]


def _get_or_create_tags(tag_names: list[str]):
    from app.models import Tag
    from app import db

    tags = []
    for name in tag_names:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags


def list_filter_choices(user_id: int) -> tuple[list[str], list[str]]:
    """Distinct categories and tag names for filter dropdowns."""
    from app.models import Note, Tag

    with app_context():
        categories = [
            c[0]
            for c in Note.query.filter_by(user_id=user_id)
            .with_entities(Note.category)
            .distinct()
            .all()
            if c[0]
        ]
        tags = [
            t.name
            for t in Tag.query.join(Note.tags).filter(Note.user_id == user_id).distinct().all()
        ]
        return categories, tags


def query_notes(
    user_id: int,
    *,
    archived: bool,
    pinned_only: bool,
    category: str,
    tag: str,
    page: int,
    per_page: int = 12,
):
    """Mirror notes.list_notes filters + order; returns (items, total)."""
    from app.models import Note, Tag

    with app_context():
        query = Note.query.filter_by(user_id=user_id, is_archived=archived)
        if pinned_only:
            query = query.filter_by(is_pinned=True)
        if category:
            query = query.filter_by(category=category)
        if tag:
            query = query.join(Note.tags).filter(Tag.name == tag)

        total = query.count()
        items = (
            query.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        # Detach-friendly: access attributes inside context if needed;
        # SQLAlchemy expire_on_commit may lazy-load later — keep session open
        # by touching relations we need on the card.
        for n in items:
            _ = list(n.tags)
            _ = n.updated_at, n.category, n.title, n.content, n.is_pinned
        return items, total


def get_note(user_id: int, note_id: int):
    from app.models import Note

    with app_context():
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if note is None:
            raise LookupError(f"Note {note_id} not found")
        related = note.get_related_notes(limit=5, min_similarity=0.0)
        # materialize
        _ = list(note.tags)
        related_mat = []
        for other, sim, rel_type in related:
            _ = list(other.tags)
            related_mat.append((other, sim, rel_type))
        return note, related_mat


def create_note(
    user_id: int,
    *,
    title: str,
    content: str,
    category: str | None,
    tags: str,
    is_pinned: bool = False,
):
    from app import db
    from app.models import Note
    from app.services.similarity_service import update_relationships_for_note
    from background_indexing_streamlit import queue_embedding_generation_streamlit

    with app_context():
        note = Note(
            user_id=user_id,
            title=title,
            content=content,
            category=category or None,
            source_type="manual",
            is_pinned=is_pinned,
        )
        db.session.add(note)
        db.session.flush()
        tag_names = _parse_tags(tags)
        if tag_names:
            note.tags = _get_or_create_tags(tag_names)
        db.session.commit()
        note_id = note.id

    try:
        with app_context():
            from app.models import Note as N

            note = db_get_note(note_id)
            update_relationships_for_note(note)
    except Exception as exc:
        return note_id, f"Note saved, but AI analysis failed: {exc}"

    queue_embedding_generation_streamlit(note_id)
    return note_id, None


def db_get_note(note_id: int):
    from app.models import Note

    from app import db as _db

    return _db.session.get(Note, note_id)


def update_note(
    user_id: int,
    note_id: int,
    *,
    title: str,
    content: str,
    category: str | None,
    tags: str,
    is_pinned: bool,
):
    from app import db
    from app.models import Note
    from app.services.similarity_service import update_relationships_for_note
    from background_indexing_streamlit import queue_embedding_generation_streamlit

    with app_context():
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if note is None:
            raise LookupError(f"Note {note_id} not found")
        note.title = title
        note.content = content
        note.category = category or None
        note.is_pinned = is_pinned
        note.tags = _get_or_create_tags(_parse_tags(tags))
        db.session.commit()

    try:
        with app_context():
            from app import db as _db

            note = _db.session.get(Note, note_id)
            update_relationships_for_note(note)
    except Exception as exc:
        queue_embedding_generation_streamlit(note_id)
        return f"Note updated, but AI analysis failed: {exc}"

    queue_embedding_generation_streamlit(note_id)
    return None


def delete_note(user_id: int, note_id: int) -> None:
    from app import db
    from app.models import Note
    from app.services.embedding_service import invalidate_embedding_cache

    with app_context():
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if note is None:
            raise LookupError(f"Note {note_id} not found")
        db.session.delete(note)
        db.session.commit()
    invalidate_embedding_cache(note_id)


def toggle_archive(user_id: int, note_id: int) -> str:
    """Return 'archived' or 'unarchived'."""
    from app import db
    from app.models import Note, Relationship
    from app.services.similarity_service import update_relationships_for_note

    with app_context():
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if note is None:
            raise LookupError(f"Note {note_id} not found")
        note.is_archived = not note.is_archived
        if note.is_archived:
            Relationship.query.filter(
                (Relationship.source_note_id == note.id)
                | (Relationship.target_note_id == note.id)
            ).delete(synchronize_session=False)
            db.session.commit()
            return "archived"
        db.session.commit()
        try:
            from app import db as _db

            note = _db.session.get(Note, note_id)
            update_relationships_for_note(note)
        except Exception:
            pass
        return "unarchived"


def toggle_pin(user_id: int, note_id: int) -> bool:
    from app import db
    from app.models import Note

    with app_context():
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if note is None:
            raise LookupError(f"Note {note_id} not found")
        note.is_pinned = not note.is_pinned
        db.session.commit()
        return note.is_pinned


class _UploadAdapter:
    """Adapt Streamlit UploadedFile to the file-like API document_service expects."""

    def __init__(self, upload):
        self.filename = getattr(upload, "name", "") or ""
        self._buf = io.BytesIO(upload.getvalue())

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._buf.seek(offset, whence)

    def tell(self) -> int:
        return self._buf.tell()

    def read(self, size: int = -1) -> bytes:
        return self._buf.read(size)


def import_document(user_id: int, upload, category: str | None) -> tuple[list[int], str | None]:
    """Validate + extract + create notes. Returns (note_ids, error)."""
    from app.services.document_service import (
        create_notes_from_document,
        extract_text,
        validate_file,
    )

    adapter = _UploadAdapter(upload)
    ok, err = validate_file(adapter)
    if not ok:
        return [], err

    try:
        adapter.seek(0)
        content = extract_text(adapter, adapter.filename)
    except Exception as exc:
        return [], f"Could not extract text from file: {exc}"

    if not content or not content.strip():
        return [], "Could not extract text from file."

    try:
        # create_notes_from_document uses Flask current_app + queue_embedding_generation
        with app_context():
            notes = create_notes_from_document(
                user_id, content, adapter.filename, category or None
            )
            ids = [n.id for n in notes]
        return ids, None
    except Exception as exc:
        return [], f"Error importing document: {exc}"
