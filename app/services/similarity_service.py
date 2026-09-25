import numpy as np

from app import db
from app.models import Note, Relationship
from app.services.embedding_service import get_all_embeddings, cosine_similarity
from app.services.keyword_service import extract_keywords
from config import Config


SIMILARITY_THRESHOLD = Config.SIMILARITY_THRESHOLD
MAX_RELATED_NOTES = Config.MAX_RELATED_NOTES
KEYWORD_THRESHOLD = Config.KEYWORD_SIMILARITY_THRESHOLD


def lightweight_similarity(note1, note2):
    """Fast, deterministic similarity that needs no external ML model.
    Used by rebuild_user_graph() as the fallback for any note that doesn't
    have a ready embedding yet."""
    words1 = set(extract_keywords(f'{note1.title} {note1.content}', max_keywords=30))
    words2 = set(extract_keywords(f'{note2.title} {note2.content}', max_keywords=30))
    keyword_score = len(words1 & words2) / max(1, len(words1 | words2))

    tags1 = {tag.name.casefold() for tag in note1.tags}
    tags2 = {tag.name.casefold() for tag in note2.tags}
    tag_score = len(tags1 & tags2) / max(1, len(tags1 | tags2)) if tags1 or tags2 else 0
    category_score = 1.0 if note1.category and note1.category == note2.category else 0

    # Tags are the strongest explicit signal; categories provide a modest boost.
    return min(1.0, (0.45 * keyword_score) + (0.40 * tag_score) + (0.15 * category_score))


def rebuild_user_graph(user_id):
    """Recompute every relationship among `user_id`'s active notes from
    scratch and replace them in one transaction.

    Notes with a ready embedding are scored against each other with a
    single vectorized cosine-similarity pass (numpy top-k - a garden of
    1,000 notes x 384 dims is ~2MB, milliseconds of work). Any note
    without a ready embedding yet (still queued, or the indexer never
    loaded a model) falls back to lightweight_similarity() for its pairs.

    This replaces the old update_relationships_for_note(), which patched
    one note's edges at a time and had to special-case "does the other
    note still want this edge on its own terms" to avoid dropping a pair
    that only the other side selected. A full, consistent rebuild scores
    every note the same way in the same pass, so that case can't arise -
    every relationship is either wanted by this rebuild or it isn't.

    Strictly scoped to one user: only that user's active notes are read,
    and only relationships between them are touched.
    """
    notes = Note.query.filter_by(user_id=user_id, is_archived=False).all()
    note_ids = [n.id for n in notes]

    if note_ids:
        Relationship.query.filter(
            Relationship.source_note_id.in_(note_ids) | Relationship.target_note_id.in_(note_ids)
        ).delete(synchronize_session=False)

    if len(notes) < 2:
        db.session.commit()
        return 0

    embeddings = get_all_embeddings(user_id)
    embedded_ids = [n.id for n in notes if n.id in embeddings]

    # (sorted note-id pair) -> (score, method). Every pair is scored from
    # exactly one side's perspective (embedded notes only ever pair with
    # other embedded notes; an unembedded note's keyword pass covers all
    # of its own pairs, including to embedded notes) and cosine similarity
    # is symmetric, so a pair can never be proposed twice with conflicting
    # scores - first write is the only write.
    pairs = {}

    def _consider(a_id, b_id, score, method):
        pair = (a_id, b_id) if a_id < b_id else (b_id, a_id)
        if pair not in pairs:
            pairs[pair] = (score, method)

    if len(embedded_ids) >= 2:
        matrix = np.stack([embeddings[nid] for nid in embedded_ids])
        sims = matrix @ matrix.T
        for i, note_id in enumerate(embedded_ids):
            row = sims[i]
            candidates = [
                (embedded_ids[j], float(row[j]))
                for j in range(len(embedded_ids))
                if j != i and row[j] >= SIMILARITY_THRESHOLD
            ]
            candidates.sort(key=lambda item: item[1], reverse=True)
            for other_id, score in candidates[:MAX_RELATED_NOTES]:
                _consider(note_id, other_id, score, 'embedding')

    unembedded = [n for n in notes if n.id not in embeddings]
    for note in unembedded:
        scored = []
        for other in notes:
            if other.id == note.id:
                continue
            score = lightweight_similarity(note, other)
            if score >= KEYWORD_THRESHOLD:
                scored.append((other.id, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        for other_id, score in scored[:MAX_RELATED_NOTES]:
            _consider(note.id, other_id, score, 'keyword')

    for (source_id, target_id), (score, method) in pairs.items():
        db.session.add(Relationship(
            source_note_id=source_id,
            target_note_id=target_id,
            similarity_score=score,
            relationship_type='semantic',
            method=method,
        ))

    db.session.commit()
    return len(pairs)


def relationship_label(rel):
    """Human-readable strength for a relationship, method-aware: keyword
    overlap and cosine similarity live on different scales, so the same
    raw number ("72%") meant different things depending which scorer
    produced it (C6). Callers show this instead of the raw score."""
    if rel.method == 'embedding':
        return 'Strong match' if rel.similarity_score >= 0.7 else 'Related'
    return 'Strong match' if rel.similarity_score >= 0.4 else 'Related'


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
