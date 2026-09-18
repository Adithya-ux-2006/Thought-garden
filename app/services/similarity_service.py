from app import db
from app.models import Note, Relationship
from app.services.embedding_service import get_all_embeddings, cosine_similarity
from app.services.keyword_service import extract_keywords
import os


SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', 0.45))
MAX_RELATED_NOTES = int(os.environ.get('MAX_RELATED_NOTES', 5))
KEYWORD_THRESHOLD = float(os.environ.get('KEYWORD_SIMILARITY_THRESHOLD', 0.18))


def lightweight_similarity(note1, note2):
    """Fast, deterministic similarity that needs no external ML model."""
    words1 = set(extract_keywords(f'{note1.title} {note1.content}', max_keywords=30))
    words2 = set(extract_keywords(f'{note2.title} {note2.content}', max_keywords=30))
    keyword_score = len(words1 & words2) / max(1, len(words1 | words2))

    tags1 = {tag.name.casefold() for tag in note1.tags}
    tags2 = {tag.name.casefold() for tag in note2.tags}
    tag_score = len(tags1 & tags2) / max(1, len(tags1 | tags2)) if tags1 or tags2 else 0
    category_score = 1.0 if note1.category and note1.category == note2.category else 0

    # Tags are the strongest explicit signal; categories provide a modest boost.
    return min(1.0, (0.45 * keyword_score) + (0.40 * tag_score) + (0.15 * category_score))


def _top_matches(note, candidates, all_embeddings):
    """Score `note` against `candidates`, return the (other_id, sim) pairs
    that qualify, strongest first, capped to MAX_RELATED_NOTES - i.e.
    exactly the set `note`'s own scoring pass would pick.

    Factored out so update_relationships_for_note() can reuse it not just
    for the note being re-scored, but also - before deleting a pair - to
    ask "would the OTHER note still pick this one, on its own terms?".
    """
    source_emb = all_embeddings.get(note.id)
    similarities = []
    for other in candidates:
        other_emb = all_embeddings.get(other.id)
        if source_emb is not None and other_emb is not None:
            sim = float(cosine_similarity(source_emb, other_emb))
            qualifies = sim >= SIMILARITY_THRESHOLD
        else:
            sim = lightweight_similarity(note, other)
            qualifies = sim >= KEYWORD_THRESHOLD
        if qualifies:
            similarities.append((other.id, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:MAX_RELATED_NOTES]


def update_relationships_for_note(note):
    if not note.content.strip():
        return

    # Never initialize/download the transformer model in a web request. If
    # embeddings already exist, use them; otherwise the lightweight scorer
    # still creates useful connections immediately.
    all_embeddings = get_all_embeddings(note.user_id, generate_if_missing=False)
    other_notes = Note.query.filter(
        Note.user_id == note.user_id,
        Note.id != note.id,
        Note.is_archived == False,
    ).all()
    notes_by_id = {n.id: n for n in other_notes}

    similarities = _top_matches(note, other_notes, all_embeddings)

    existing_rels = Relationship.query.filter(
        (Relationship.source_note_id == note.id) | (Relationship.target_note_id == note.id)
    ).all()

    existing_pairs = set()
    for rel in existing_rels:
        pair = tuple(sorted([rel.source_note_id, rel.target_note_id]))
        existing_pairs.add(pair)

    selected_pairs = {tuple(sorted((note.id, other_id))) for other_id, _ in similarities}
    for rel in existing_rels:
        pair = tuple(sorted((rel.source_note_id, rel.target_note_id)))
        if pair in selected_pairs:
            continue

        # This pair isn't in `note`'s own top picks anymore, but a
        # relationship can exist because the OTHER note ranked THIS one
        # highly - re-scoring A must not delete an edge that belongs to
        # B's top-N just because A stopped wanting it. Recompute the other
        # note's own ranking (its own candidates, on its own terms) before
        # deleting; only drop the row if neither side wants it.
        other_id = rel.target_note_id if rel.source_note_id == note.id else rel.source_note_id
        other_note = notes_by_id.get(other_id)
        if other_note is None:
            # Other note archived/gone from this candidate set - nothing
            # left to keep the edge for.
            db.session.delete(rel)
            continue

        other_candidates = [note] + [n for n in other_notes if n.id != other_id]
        other_top = _top_matches(other_note, other_candidates, all_embeddings)
        still_wanted_by_other = any(oid == note.id for oid, _ in other_top)
        if not still_wanted_by_other:
            db.session.delete(rel)

    new_pairs = set()
    for other_id, sim in similarities:
        pair = tuple(sorted([note.id, other_id]))
        if pair in existing_pairs:
            rel = Relationship.query.filter(
                ((Relationship.source_note_id == note.id) & (Relationship.target_note_id == other_id)) |
                ((Relationship.source_note_id == other_id) & (Relationship.target_note_id == note.id))
            ).first()
            if rel:
                rel.similarity_score = sim
                rel.updated_at = db.func.now()
        else:
            new_pairs.add((note.id, other_id, sim))
    
    for source_id, target_id, sim in new_pairs:
        rel = Relationship(
            source_note_id=source_id,
            target_note_id=target_id,
            similarity_score=sim,
            relationship_type='semantic'
        )
        db.session.add(rel)
    
    db.session.commit()


def recalculate_all_relationships(user_id):
    notes = Note.query.filter_by(user_id=user_id).all()
    for note in notes:
        update_relationships_for_note(note)


def ensure_all_relationships():
    """Backfill connections for every existing garden during application startup."""
    user_ids = [row[0] for row in db.session.query(Note.user_id).distinct().all()]
    note_count = 0
    for user_id in user_ids:
        notes = Note.query.filter_by(user_id=user_id, is_archived=False).all()
        note_count += len(notes)
        for note in notes:
            update_relationships_for_note(note)
    return note_count, Relationship.query.count()


def get_relationship_explanation(note1, note2):
    # max_keywords explicit: this module previously had its own
    # extract_keywords() defaulting to 10, vs keyword_service's default
    # of 5 - pin it here so consolidating the two didn't quietly change
    # what "common keywords" means for this explanation text.
    keywords1 = set(extract_keywords(note1.title + ' ' + note1.content, max_keywords=10))
    keywords2 = set(extract_keywords(note2.title + ' ' + note2.content, max_keywords=10))
    common = keywords1 & keywords2
    
    common_tags = set(t.name.lower() for t in note1.tags) & set(t.name.lower() for t in note2.tags)
    common.update(common_tags)
    
    if common:
        top_common = sorted(list(common))[:5]
        return f"Connected because both notes discuss: {', '.join(top_common)}."
    return "Semantically related based on overall content similarity."
