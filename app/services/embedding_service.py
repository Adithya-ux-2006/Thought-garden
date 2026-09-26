import hashlib

import numpy as np
from app import db
from app.models import Note, NoteEmbedding
from config import Config

_model = None
_model_name = Config.EMBEDDING_MODEL


def cosine_similarity(a, b):
    """Shared by similarity_service and search_service."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def get_model():
    """Load (once) and return the sentence-transformer model.

    Only the background indexer worker (app/services/indexer.py) calls
    this, at process startup. Request-handling code must never call it -
    loading the model takes ~14s and would block the request. Code
    that runs on a request thread should use get_ready_model() instead,
    which returns whatever is already loaded (possibly None) without ever
    triggering a load itself.
    """
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_model_name)
    return _model


def get_ready_model():
    """The already-loaded model, or None if the indexer hasn't loaded one
    yet (or never will, e.g. no network). Never loads anything itself -
    safe to call from a request handler."""
    return _model


def model_loaded():
    return _model is not None


def get_embedding_text(note):
    parts = [note.title, note.content]
    if note.tags:
        # Sorted so re-tagging with the same set in a different order
        # doesn't change the hash below and trigger a needless re-embed.
        parts.append(' '.join(sorted(t.name for t in note.tags)))
    if note.category:
        parts.append(note.category)
    return ' '.join(parts)


def content_hash(note):
    """Hash of the exact text generate_embedding() would encode for this
    note right now. Compared against NoteEmbedding.content_hash to decide
    whether a save actually changed anything embedding-relevant."""
    return hashlib.sha256(get_embedding_text(note).encode('utf-8')).hexdigest()


def generate_embedding(note):
    """Compute and store `note`'s embedding. Only ever called from the
    indexer worker thread (which has already loaded the model) or from a
    CLI command - never from a request handler."""
    model = get_model()
    embedding_text = get_embedding_text(note)
    embedding = model.encode(embedding_text, convert_to_numpy=True, normalize_embeddings=True)
    embedding = embedding.astype(np.float32)

    # Plain float32 bytes, not pickle: unpickling data straight out of the
    # database is a known code-execution risk if that data is ever
    # tampered with, and it buys nothing here since a raw byte dump is
    # just as fast to read back with np.frombuffer().
    embedding_blob = embedding.tobytes()
    note_hash = content_hash(note)

    row = db.session.get(NoteEmbedding, note.id)
    if row is None:
        row = NoteEmbedding(note_id=note.id, embedding=embedding_blob, content_hash=note_hash)
        db.session.add(row)
    else:
        row.embedding = embedding_blob
        row.content_hash = note_hash
    db.session.commit()

    return embedding


def _looks_like_pickle(blob):
    # Legacy rows were pickled: protocol 2-5 header and trailing STOP opcode.
    return blob[:1] == b'\x80' and blob[1:2] in (b'\x02', b'\x03', b'\x04', b'\x05') and blob[-1:] == b'.'


def _decode_embedding_blob(blob):
    """Raw float32 bytes as written by generate_embedding(), or None for
    anything else. Never unpickled: that would execute database content."""
    if not blob or len(blob) % 4 or _looks_like_pickle(blob):
        return None
    return np.frombuffer(blob, dtype=np.float32)


def get_embedding(note_id, generate_if_missing=False):
    """Read whatever's stored for `note_id`. Defaults to read-only: callers
    on a request thread must never pass generate_if_missing=True, since
    that calls generate_embedding() (and therefore get_model()) inline."""
    row = db.session.get(NoteEmbedding, note_id)

    if row is not None:
        embedding = _decode_embedding_blob(row.embedding)
        if embedding is not None:
            return embedding

    if generate_if_missing:
        note = db.session.get(Note, note_id)
        if note is not None:
            return generate_embedding(note)

    return None


def get_all_embeddings(user_id):
    """Every ready embedding for `user_id`'s notes, read straight from the
    database - no in-process cache. Notes without a usable embedding yet
    (still queued, or the indexer isn't ready) are simply absent from the
    result; callers fall back to keyword scoring for those."""
    rows = (
        db.session.query(NoteEmbedding)
        .join(Note, NoteEmbedding.note_id == Note.id)
        .filter(Note.user_id == user_id)
        .all()
    )
    embeddings = {}
    for row in rows:
        embedding = _decode_embedding_blob(row.embedding)
        if embedding is not None:
            embeddings[row.note_id] = embedding
    return embeddings
