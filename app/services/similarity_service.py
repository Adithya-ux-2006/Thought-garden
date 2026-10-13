import math

import numpy as np

from app import db
from app.models import Note, Relationship
from app.services.embedding_service import get_all_embeddings, cosine_similarity
from app.services.keyword_service import extract_keywords
from config import Config
from tg_ui import categories as palette


SIMILARITY_THRESHOLD = Config.SIMILARITY_THRESHOLD
MAX_RELATED_NOTES = Config.MAX_RELATED_NOTES
KEYWORD_THRESHOLD = Config.KEYWORD_SIMILARITY_THRESHOLD

# What the user said explicitly counts alongside what the model infers:
# embedding pairs get a bonus for shared tags and a shared category before
# the threshold/top-N cut. Without it, two notes both tagged "Databases"
# whose wording differs (cosine ~0.2) never connected. A shared tag is
# worth more the rarer it is in the garden (a tag on 2 notes counts in
# full, one on most notes - "exam prep" - barely), so broad tags don't wire
# everything together. Tuned on a simulated 28-note study + creative
# garden: 12 -> 32 edges, isolated notes 15 -> 4, no spurious links.
SHARED_TAG_BONUS = 0.20
SHARED_TAG_BONUS_CAP = 0.25
SAME_CATEGORY_BONUS = 0.05


def tag_weights(notes):
    """{casefolded tag: 0..1} - inverse document frequency, normalised so a
    tag shared by exactly two notes weighs 1.0."""
    counts = {}
    for note in notes:
        for name in {t.name.casefold() for t in note.tags}:
            counts[name] = counts.get(name, 0) + 1
    n = len(notes)
    if n <= 2:
        return {name: 1.0 for name in counts}
    scale = math.log(n / 2)
    return {name: max(0.0, min(1.0, math.log(n / c) / scale)) for name, c in counts.items()}


def same_category(a, b):
    """Both notes filed under the same category - by exact text or by the
    shared palette (a retired 'Cybersecurity' note and a 'Study' note are
    both Study). Two notes with no category don't count."""
    if not a or not b:
        return False
    if a.casefold() == b.casefold():
        return True
    branded = palette.resolve(a)
    return branded is not None and branded is palette.resolve(b)


MAX_EXPLICIT_BONUS = SHARED_TAG_BONUS_CAP + SAME_CATEGORY_BONUS


def explicit_bonus(tags_a, category_a, tags_b, category_b, weights):
    """Score bonus from the user's own organisation of two notes (tag sets
    are casefolded names)."""
    bonus = min(SHARED_TAG_BONUS * sum(weights.get(t, 0.0) for t in tags_a & tags_b), SHARED_TAG_BONUS_CAP)
    if same_category(category_a, category_b):
        bonus += SAME_CATEGORY_BONUS
    return bonus


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

    A full rebuild scores every note the same way in the same pass, so the
    result doesn't depend on the order notes were edited in.

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
        by_id = {n.id: n for n in notes}
        weights = tag_weights(notes)
        tagsets = {nid: frozenset(t.name.casefold() for t in by_id[nid].tags) for nid in embedded_ids}
        categories = {nid: by_id[nid].category for nid in embedded_ids}
        # Only pairs that could still reach the threshold with the largest
        # possible bonus are scored in Python; the rest stay vectorized.
        floor = SIMILARITY_THRESHOLD - MAX_EXPLICIT_BONUS
        for i, note_id in enumerate(embedded_ids):
            row = sims[i]
            candidates = []
            for j in np.nonzero(row >= floor)[0]:
                if j == i:
                    continue
                other_id = embedded_ids[j]
                score = min(1.0, float(row[j]) + explicit_bonus(
                    tagsets[note_id], categories[note_id], tagsets[other_id], categories[other_id], weights))
                if score >= SIMILARITY_THRESHOLD:
                    candidates.append((other_id, score))
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
    overlap and cosine similarity live on different scales, so a raw
    percentage isn't comparable across methods. Callers show this instead
    of the raw score."""
    if rel.method == 'embedding':
        return 'Strong match' if rel.similarity_score >= 0.7 else 'Related'
    return 'Strong match' if rel.similarity_score >= 0.4 else 'Related'


def explain_connection(note, other, rel):
    """Why `note` and `other` are linked by the stored relationship `rel`.

    Describes the signals behind the existing edge; it never rescores the pair.
    """
    other_tag_keys = {t.name.casefold() for t in other.tags}
    shared_tags = sorted({t.name for t in note.tags if t.name.casefold() in other_tag_keys},
                         key=str.casefold)[:5]

    keywords = set(extract_keywords(f'{note.title} {note.content}', max_keywords=10))
    other_keywords = set(extract_keywords(f'{other.title} {other.content}', max_keywords=10))
    tag_keys = {t.casefold() for t in shared_tags}
    shared_keywords = sorted(k for k in keywords & other_keywords if k not in tag_keys)[:5]

    same_category = note.category if note.category and note.category == other.category else None

    parts = []
    if shared_tags:
        parts.append(f"Shared tags: {', '.join(shared_tags)}.")
    if shared_keywords:
        parts.append(f"Both mention: {', '.join(shared_keywords)}.")
    if same_category:
        parts.append(f'Both in {same_category}.')
    if not parts:
        parts.append('Similar overall meaning.' if rel.method == 'embedding' else 'Overlapping wording.')

    return {
        'label': relationship_label(rel),
        'method': rel.method,
        'basis': 'Similar meaning' if rel.method == 'embedding' else 'Keyword overlap',
        'shared_tags': shared_tags,
        'shared_keywords': shared_keywords,
        'same_category': same_category,
        'reason': ' '.join(parts),
    }
