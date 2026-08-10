import os
import pickle
import numpy as np
from app import db
from app.models import Note
from sqlalchemy import text

_model = None
_model_name = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
_embedding_cache = {}


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_model_name)
    return _model


def get_embedding_text(note):
    parts = [note.title, note.content]
    if note.tags:
        parts.append(' '.join([t.name for t in note.tags]))
    if note.category:
        parts.append(note.category)
    return ' '.join(parts)


def generate_embedding(note):
    model = get_model()
    embedding_text = get_embedding_text(note)
    embedding = model.encode(embedding_text, convert_to_numpy=True, normalize_embeddings=True)
    
    embedding_blob = pickle.dumps(embedding.astype(np.float32))
    
    db.session.execute(
        text("INSERT OR REPLACE INTO note_embeddings (note_id, embedding, updated_at) VALUES (:note_id, :embedding, datetime('now'))"),
        {'note_id': note.id, 'embedding': embedding_blob}
    )
    db.session.commit()
    
    _embedding_cache[note.id] = embedding
    return embedding


def get_embedding(note_id, generate_if_missing=True):
    if note_id in _embedding_cache:
        return _embedding_cache[note_id]
    
    result = db.session.execute(
        text("SELECT embedding FROM note_embeddings WHERE note_id = :note_id"),
        {'note_id': note_id}
    ).fetchone()
    
    if result:
        embedding = pickle.loads(result[0])
        _embedding_cache[note_id] = embedding
        return embedding
    
    note = db.session.get(Note, note_id)
    if note and generate_if_missing:
        return generate_embedding(note)
    
    return None


def clear_embedding_cache():
    global _embedding_cache
    _embedding_cache.clear()


def get_all_embeddings(user_id, generate_if_missing=True):
    notes = Note.query.filter_by(user_id=user_id).all()
    embeddings = {}
    for note in notes:
        emb = get_embedding(note.id, generate_if_missing=generate_if_missing)
        if emb is not None:
            embeddings[note.id] = emb
    return embeddings
