from app import db
from app.models import Note, Tag, User
from app.services.similarity_service import update_relationships_for_note


SEED_USER_EMAIL = 'demo@thoughtgarden.app'


def prepare_starter_garden(user):
    """Copy the starter garden to a new user and connect it in one flow."""
    seed_user = User.query.filter_by(email=SEED_USER_EMAIL).first()
    if seed_user is None or seed_user.id == user.id or user.notes.count():
        return 0, 0

    seed_notes = Note.query.filter_by(user_id=seed_user.id, is_archived=False).all()
    new_notes = []
    for source in seed_notes:
        note = Note(
            user_id=user.id,
            title=source.title,
            content=source.content,
            category=source.category,
            source_type='starter',
            is_pinned=source.is_pinned,
        )
        for source_tag in source.tags:
            tag = Tag.query.filter_by(name=source_tag.name).first()
            if tag is None:
                tag = Tag(name=source_tag.name)
                db.session.add(tag)
            note.tags.append(tag)
        db.session.add(note)
        new_notes.append(note)

    db.session.commit()

    # Complete connection discovery before the user enters the Garden, so the
    # first screen is coherent instead of gradually changing underneath them.
    for note in new_notes:
        update_relationships_for_note(note)

    from app.models import Relationship
    connection_count = Relationship.query.join(
        Note, Relationship.source_note_id == Note.id
    ).filter(Note.user_id == user.id).count()
    return len(new_notes), connection_count
