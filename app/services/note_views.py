"""Note view models for templates: tg_ui.presenters.note_view() plus each
note's growth stage, computed from one aggregate connection-count query
(the same count /garden/data uses, so a note's plant matches the garden)."""

from sqlalchemy import func

from app.models import Note, Relationship, db
from app.services.growth_service import compute_growth_stage
from tg_ui.presenters import note_view


def connection_counts(note_ids):
    ids = list(note_ids)
    if not ids:
        return {}
    return dict(
        db.session.query(Note.id, func.count(Relationship.id))
        .outerjoin(Relationship,
                   (Relationship.source_note_id == Note.id) | (Relationship.target_note_id == Note.id))
        .filter(Note.id.in_(ids))
        .group_by(Note.id)
        .all()
    )


def note_views(notes):
    notes = list(notes)
    counts = connection_counts(n.id for n in notes)
    return [
        note_view(n, stage=compute_growth_stage(n.created_at, counts.get(n.id, 0)),
                  connections=counts.get(n.id, 0))
        for n in notes
    ]


def single_note_view(note):
    return note_views([note])[0]
