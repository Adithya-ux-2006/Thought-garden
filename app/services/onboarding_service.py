from app.models import Note, Relationship, User
from app.services.note_lifecycle_service import create_note_batch


SEED_USER_EMAIL = 'demo@thoughtgarden.app'


def prepare_starter_garden(user):
    """Copy the starter garden to a new user and connect it in one flow."""
    seed_user = User.query.filter_by(email=SEED_USER_EMAIL).first()
    if seed_user is None or seed_user.id == user.id or user.notes.count():
        return 0, 0

    seed_notes = Note.query.filter_by(user_id=seed_user.id, is_archived=False).all()
    result = create_note_batch(user.id, [
        {
            'title': source.title,
            'content': source.content,
            'category': source.category,
            'source_type': 'starter',
            'is_pinned': source.is_pinned,
            'tags': [tag.name for tag in source.tags],
        }
        for source in seed_notes
    ])
    new_notes = result.notes

    connection_count = Relationship.query.join(
        Note, Relationship.source_note_id == Note.id
    ).filter(Note.user_id == user.id).count()
    return len(new_notes), connection_count
