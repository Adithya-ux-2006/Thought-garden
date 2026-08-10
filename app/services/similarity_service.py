import numpy as np
from app import db
from app.models import Note, Relationship
from app.services.embedding_service import get_embedding, get_all_embeddings
import os


SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', 0.45))
MAX_RELATED_NOTES = int(os.environ.get('MAX_RELATED_NOTES', 5))
KEYWORD_THRESHOLD = float(os.environ.get('KEYWORD_SIMILARITY_THRESHOLD', 0.18))


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


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


def update_relationships_for_note(note):
    if not note.content.strip():
        return
    
    # Never initialize/download the transformer model in a web request. If
    # embeddings already exist, use them; otherwise the lightweight scorer
    # still creates useful connections immediately.
    source_emb = get_embedding(note.id, generate_if_missing=False)
    all_embeddings = get_all_embeddings(note.user_id, generate_if_missing=False)
    other_notes = Note.query.filter(
        Note.user_id == note.user_id,
        Note.id != note.id,
        Note.is_archived == False,
    ).all()
    
    similarities = []
    for other in other_notes:
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
    similarities = similarities[:MAX_RELATED_NOTES]
    
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
        if pair not in selected_pairs:
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
    keywords1 = set(extract_keywords(note1.title + ' ' + note1.content))
    keywords2 = set(extract_keywords(note2.title + ' ' + note2.content))
    common = keywords1 & keywords2
    
    common_tags = set(t.name.lower() for t in note1.tags) & set(t.name.lower() for t in note2.tags)
    common.update(common_tags)
    
    if common:
        top_common = sorted(list(common))[:5]
        return f"Connected because both notes discuss: {', '.join(top_common)}."
    return "Semantically related based on overall content similarity."


def extract_keywords(text, max_keywords=10):
    import re
    from collections import Counter
    
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him',
        'us', 'them', 'what', 'which', 'who', 'whom', 'whose', 'where',
        'when', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'now', 'then', 'also', 'well', 'even'
    }
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    words = [w for w in words if w not in stop_words]
    
    freq = Counter(words)
    return [word for word, _ in freq.most_common(max_keywords)]
