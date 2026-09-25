import json
import os
from datetime import datetime, timedelta, timezone

from app import db
from app.models import Note, Relationship
from app.services import indexer
from app.services.similarity_service import rebuild_user_graph
from app.services.tag_service import get_or_create_tags

STARTER_NOTES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'starter_notes.json')


def load_starter_notes():
    with open(STARTER_NOTES_PATH, encoding='utf-8') as f:
        return json.load(f)


def add_starter_notes(user, source_type='starter', backdate=False):
    """Create the starter notes for `user` from the bundled fixture and
    discover their connections. `backdate` applies each note's `days_old`."""
    new_notes = []
    for item in load_starter_notes():
        note = Note(
            user_id=user.id,
            title=item['title'],
            content=item['content'],
            category=item.get('category'),
            source_type=source_type,
            is_pinned=item.get('is_pinned', False),
        )
        if backdate and item.get('days_old'):
            note.created_at = datetime.now(timezone.utc) - timedelta(days=item['days_old'])
        note.tags = get_or_create_tags(user.id, item.get('tags', []))
        db.session.add(note)
        new_notes.append(note)
    db.session.commit()

    # Connect everything before the user first sees the garden, then queue
    # each note for embedding so the background worker can upgrade these
    # keyword-tier connections once it gets to them.
    rebuild_user_graph(user.id)
    for note in new_notes:
        indexer.enqueue(note)
    return new_notes


def prepare_starter_garden(user):
    """Give a brand-new user the starter garden; returns (notes, connections)."""
    if user.notes.count():
        return 0, 0
    new_notes = add_starter_notes(user)
    if not new_notes:
        return 0, 0
    connection_count = Relationship.query.join(
        Note, Relationship.source_note_id == Note.id
    ).filter(Note.user_id == user.id).count()
    return len(new_notes), connection_count
