from app import db
from app.models import Note, Tag
from app.services.embedding_service import get_embedding, get_all_embeddings, cosine_similarity
from app.services.pagination import SimplePagination
from sqlalchemy import or_, func


def keyword_search(user_id, query, category=None, tag=None, source_type=None, page=1, per_page=10):
    q = Note.query.filter_by(user_id=user_id, is_archived=False)
    
    if query:
        search_term = f'%{query}%'
        q = q.filter(or_(
            Note.title.ilike(search_term),
            Note.content.ilike(search_term)
        ))
    
    if category:
        q = q.filter_by(category=category)
    
    if tag:
        q = q.join(Note.tags).filter(Tag.name == tag)
    
    if source_type:
        q = q.filter_by(source_type=source_type)
    
    return q.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).paginate(page=page, per_page=per_page)


def semantic_search(user_id, query, category=None, tag=None, source_type=None, page=1, per_page=10, min_similarity=0.5):
    if not query:
        return Note.query.filter_by(id=-1).paginate(page=page, per_page=per_page)
    
    from app.services.embedding_service import get_model
    model = get_model()
    query_emb = model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
    
    all_embeddings = get_all_embeddings(user_id)
    
    similarities = []
    for note_id, emb in all_embeddings.items():
        sim = cosine_similarity(query_emb, emb)
        if sim >= min_similarity:
            similarities.append((note_id, sim))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    if not similarities:
        return Note.query.filter_by(id=-1).paginate(page=page, per_page=per_page)
    
    note_ids = [nid for nid, _ in similarities]
    
    q = Note.query.filter(Note.id.in_(note_ids), Note.user_id == user_id, Note.is_archived == False)
    
    if category:
        q = q.filter_by(category=category)
    if tag:
        q = q.join(Note.tags).filter(Tag.name == tag)
    if source_type:
        q = q.filter_by(source_type=source_type)
    
    notes = q.all()
    note_dict = {n.id: n for n in notes}
    
    sorted_notes = [note_dict[nid] for nid, _ in similarities if nid in note_dict]

    start = (page - 1) * per_page
    end = start + per_page
    page_items = sorted_notes[start:end]

    return SimplePagination(page_items, page, per_page, len(sorted_notes))


def hybrid_search(user_id, query, category=None, tag=None, source_type=None, page=1, per_page=10):
    # Depth of each sub-search must cover however far the caller is paginating,
    # or results/total past that depth are silently unreachable/wrong. Cap at
    # 1000 since this is a personal notes app, not to bound a truly expensive
    # query - semantic_search's dominant cost (model encode + scoring every
    # embedding) doesn't scale with per_page, and keyword_search's LIMIT is cheap
    # at this size.
    fetch_depth = min(max(page * per_page, 50), 1000)
    keyword_results = keyword_search(user_id, query, category, tag, source_type, page=1, per_page=fetch_depth)
    semantic_results = semantic_search(user_id, query, category, tag, source_type, page=1, per_page=fetch_depth)

    # Reciprocal Rank Fusion: a standard way to merge two ranked lists
    # without needing their scores to be on the same scale (a keyword
    # match and a cosine similarity aren't comparable numbers). Replaces
    # the previous "1.0 - rank*0.02" fudge, which wasn't grounded in
    # anything and degrades badly past ~50 results (goes negative).
    # k=60 is the standard constant from the RRF literature.
    RRF_K = 60
    combined = {}

    for i, note in enumerate(keyword_results.items):
        combined[note.id] = combined.get(note.id, 0) + 1.0 / (RRF_K + i + 1)

    for i, note in enumerate(semantic_results.items):
        combined[note.id] = combined.get(note.id, 0) + 1.0 / (RRF_K + i + 1)

    sorted_ids = sorted(combined.keys(), key=lambda x: combined[x], reverse=True)

    notes = Note.query.filter(Note.id.in_(sorted_ids), Note.user_id == user_id).all()
    note_dict = {n.id: n for n in notes}
    sorted_notes = [note_dict[nid] for nid in sorted_ids if nid in note_dict]

    start = (page - 1) * per_page
    end = start + per_page
    page_items = sorted_notes[start:end]

    return SimplePagination(page_items, page, per_page, len(sorted_notes))