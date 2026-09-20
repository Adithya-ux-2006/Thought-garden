"""Small, local knowledge utilities that work without external AI services."""

import re
from collections import defaultdict

from app.models import Note, Relationship


def summarize_note(note, sentence_limit=3):
    sentences = re.split(r'(?<=[.!?])\s+', note.content.strip())
    summary = ' '.join(sentences[:sentence_limit]).strip()
    return summary or note.content[:400]


def make_flashcards(note, limit=4):
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', note.content) if len(s.strip()) > 25]
    cards = []
    for index, sentence in enumerate(sentences[:limit], 1):
        cards.append({
            'question': f'What is an important idea from “{note.title}” (#{index})?',
            'answer': sentence,
        })
    return cards


def duplicate_candidates(user_id, threshold=0.82):
    return Relationship.query.join(
        Note, Relationship.source_note_id == Note.id
    ).filter(
        Note.user_id == user_id,
        Relationship.similarity_score >= threshold,
    ).order_by(Relationship.similarity_score.desc()).all()


def garden_health(user_id):
    notes = Note.query.filter_by(user_id=user_id, is_archived=False).all()
    note_ids = {note.id for note in notes}
    relationships = Relationship.query.filter(
        Relationship.source_note_id.in_(note_ids),
        Relationship.target_note_id.in_(note_ids),
    ).all() if note_ids else []

    adjacency = defaultdict(set)
    for relationship in relationships:
        adjacency[relationship.source_note_id].add(relationship.target_note_id)
        adjacency[relationship.target_note_id].add(relationship.source_note_id)

    orphans = [note for note in notes if not adjacency[note.id]]
    roots = sorted(
        (note for note in notes if adjacency[note.id]),
        key=lambda note: len(adjacency[note.id]), reverse=True,
    )[:5]
    components = 0
    unseen = set(note_ids)
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            current = stack.pop()
            neighbours = adjacency[current] & unseen
            unseen -= neighbours
            stack.extend(neighbours)

    connected_count = len(notes) - len(orphans)
    score = round((connected_count / len(notes) * 100), 0) if notes else 0
    return {
        'total_notes': len(notes),
        'connections': len(relationships),
        'orphans': orphans,
        'roots': roots,
        'components': components,
        'score': int(score),
    }


def export_garden(user_id):
    notes = Note.query.filter_by(user_id=user_id).order_by(Note.created_at).all()
    health = garden_health(user_id)
    return {
        'notes': [{
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'summary': summarize_note(note),
            'category': note.category,
            'tags': [tag.name for tag in note.tags],
            'source_type': note.source_type,
            'created_at': note.created_at.isoformat() if note.created_at else None,
        } for note in notes],
        'health': {
            'total_notes': health['total_notes'],
            'connections': health['connections'],
            'components': health['components'],
            'score': health['score'],
            'root_note_ids': [note.id for note in health['roots']],
            'orphan_note_ids': [note.id for note in health['orphans']],
        },
    }
