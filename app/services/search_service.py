from app import db
from app.models import Note, Tag
from app.services.embedding_service import get_embedding, get_all_embeddings
from sqlalchemy import or_, func
import numpy as np


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


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
    
    from app import db
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
    
    start = (page - 1) * per_page
    end = start + per_page
    page_items = sorted_notes[start:end]
    
    return Pagination(page_items, page, per_page, len(sorted_notes))


def hybrid_search(user_id, query, category=None, tag=None, source_type=None, page=1, per_page=10):
    keyword_results = keyword_search(user_id, query, category, tag, source_type, page=1, per_page=50)
    semantic_results = semantic_search(user_id, query, category, tag, source_type, page=1, per_page=50)
    
    combined = {}
    
    for i, note in enumerate(keyword_results.items):
        score = 1.0 - (i * 0.02)
        combined[note.id] = combined.get(note.id, 0) + score
    
    for i, note in enumerate(semantic_results.items):
        score = 1.0 - (i * 0.02)
        combined[note.id] = combined.get(note.id, 0) + score
    
    sorted_ids = sorted(combined.keys(), key=lambda x: combined[x], reverse=True)
    
    notes = Note.query.filter(Note.id.in_(sorted_ids)).all()
    note_dict = {n.id: n for n in notes}
    sorted_notes = [note_dict[nid] for nid in sorted_ids if nid in note_dict]
    
    from app import db
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
        
        def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num > self.page - left_current - 1 and num < self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
    
    start = (page - 1) * per_page
    end = start + per_page
    page_items = sorted_notes[start:end]
    
    return Pagination(page_items, page, per_page, len(sorted_notes))