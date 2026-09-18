import os
import pickle
import numpy as np
from app import db
from app.models import Note, NoteEmbedding

_model = None
_model_name = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
_embedding_cache = {}


def cosine_similarity(a, b):
    """Shared by similarity_service and search_service - previously
    defined separately (identically) in both files."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


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
    embedding = embedding.astype(np.float32)

    # Plain float32 bytes, not pickle: unpickling data straight out of the
    # database is a known code-execution risk if that data is ever
    # tampered with, and it buys nothing here since a raw byte dump is
    # just as fast to read back with np.frombuffer().
    embedding_blob = embedding.tobytes()

    row = db.session.get(NoteEmbedding, note.id)
    if row is None:
        row = NoteEmbedding(note_id=note.id, embedding=embedding_blob)
        db.session.add(row)
    else:
        row.embedding = embedding_blob
    db.session.commit()

    _embedding_cache[note.id] = embedding
    return embedding


def _decode_embedding_blob(blob):
    """Read back an embedding stored by generate_embedding(). Falls back
    to unpickling for rows written before the pickle -> raw-bytes switch,
    so existing databases don't need a migration to keep working.

    Pickle protocol 2+ (what pickle.dumps uses by default since Python
    3.8) always starts with the byte 0x80, which raw float32 data from
    a unit-normalized embedding essentially never does - but checking
    is cheap and correct either way, whereas trying frombuffer() first
    and catching ValueError is NOT reliable: pickled bytes are still
    "valid" bytes, so frombuffer() happily reinterprets them as the
    wrong number of nonsense floats instead of raising.
    """
    if blob[:1] == b'\x80':
        return pickle.loads(blob)
    return np.frombuffer(blob, dtype=np.float32)


def get_embedding(note_id, generate_if_missing=True):
    if note_id in _embedding_cache:
        return _embedding_cache[note_id]

    row = db.session.get(NoteEmbedding, note_id)

    if row is not None:
        embedding = _decode_embedding_blob(row.embedding)
        _embedding_cache[note_id] = embedding
        return embedding

    note = db.session.get(Note, note_id)
    if note and generate_if_missing:
        return generate_embedding(note)

    return None


def clear_embedding_cache():
    global _embedding_cache
    _embedding_cache.clear()


def invalidate_embedding_cache(note_id):
    """Drop a single note's cached embedding. Needed on delete: the
    note_embeddings row cascades away via the ORM relationship, but the
    in-process cache doesn't know that on its own and would otherwise
    keep serving a stale vector for a note_id that no longer exists."""
    _embedding_cache.pop(note_id, None)


def get_all_embeddings(user_id, generate_if_missing=True):
    notes = Note.query.filter_by(user_id=user_id).all()
    embeddings = {}
    for note in notes:
        emb = get_embedding(note.id, generate_if_missing=generate_if_missing)
        if emb is not None:
            embeddings[note.id] = emb
    return embeddings
