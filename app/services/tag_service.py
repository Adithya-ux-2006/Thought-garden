from app import db
from app.models import Tag


def get_or_create_tags(user_id, tag_names):
    """Case-insensitive per-user lookup-or-create.

    Tags are scoped per user (see Tag's uq_tag_user_id_name_lower index),
    so a duplicate can only collide within the same user's tags. Preserves
    whichever casing was saved first for a given name; also de-duplicates
    within `tag_names` itself, since e.g. submitting "AI, ai" in one note's
    tag field would otherwise try to insert two rows that collide on the
    same case-insensitive unique index.
    """
    tags = []
    seen = set()
    for raw_name in tag_names:
        name = raw_name.strip()
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())
        tag = Tag.query.filter_by(user_id=user_id).filter(
            db.func.lower(Tag.name) == name.lower()).first()
        if tag is None:
            tag = Tag(user_id=user_id, name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags


def prune_orphan_tags(user_id):
    """Delete this user's tags no longer attached to any note. Tags are
    scoped per user, so a tag with no notes left is a genuine orphan."""
    orphans = Tag.query.filter_by(user_id=user_id).filter(~Tag.notes.any()).all()
    for tag in orphans:
        db.session.delete(tag)
