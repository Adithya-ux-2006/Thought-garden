import html
import re

from markupsafe import Markup
from sqlalchemy import text

from app import db
from app.models import Note, Tag
from app.services import indexer
from app.services.embedding_service import get_all_embeddings, get_ready_model, cosine_similarity
from app.services.pagination import SimplePagination

# snippet() markers: control characters that can't appear in normal note
# text and have no meaning to html.escape(). _snippet_markup() escapes the
# raw snippet first (so any HTML/script a note's own content happens to
# contain is neutralized), then swaps these for real <mark> tags - the
# <mark> tags themselves are never at risk of being escaped or of
# containing unescaped user content, since they're substituted in after
# escaping.
_SNIPPET_START = '\x01'
_SNIPPET_END = '\x02'


def _fts_tokens(query):
    return re.findall(r'[A-Za-z0-9]+', query)


def _fts_match_expr(tokens):
    # Every token is individually double-quoted, which makes FTS5 treat it
    # as a literal string rather than a query-syntax token. This matters
    # for two reasons: it's the only thing standing between raw user input
    # and SQLite's MATCH query syntax (AND/OR/NOT/NEAR/^/-/*), and without
    # it a search for a word like "or" would silently become the boolean
    # operator instead of a search term.
    return ' OR '.join(f'"{t}"' for t in tokens)


def _snippet_markup(raw_snippet):
    if raw_snippet is None:
        return None
    escaped = html.escape(raw_snippet)
    highlighted = escaped.replace(_SNIPPET_START, '<mark>').replace(_SNIPPET_END, '</mark>')
    return Markup(highlighted)


def _fts_search(user_id, query, category, tag, source_type, page, per_page):
    """FTS5-backed keyword search: bm25() ranking, snippet() highlighting.
    Returns a SimplePagination of Note objects, each with a `.snippet`
    Markup attribute set from the match."""
    tokens = _fts_tokens(query)
    if not tokens:
        return SimplePagination([], page, per_page, 0)

    filters = ['note.user_id = :user_id', 'note.is_archived = 0']
    params = {'user_id': user_id, 'match': _fts_match_expr(tokens)}

    if category:
        filters.append('note.category = :category')
        params['category'] = category
    if source_type:
        filters.append('note.source_type = :source_type')
        params['source_type'] = source_type

    tag_join = ''
    if tag:
        tag_join = 'JOIN note_tags nt ON nt.note_id = note.id JOIN tag ON tag.id = nt.tag_id AND tag.name = :tag'
        params['tag'] = tag

    where_sql = ' AND '.join(filters)
    from_sql = f'FROM note_fts JOIN note ON note.id = note_fts.rowid {tag_join} WHERE note_fts MATCH :match AND {where_sql}'

    total = db.session.execute(text(f'SELECT COUNT(*) {from_sql}'), params).scalar()

    offset = (page - 1) * per_page
    rows = db.session.execute(
        text(f"""
            SELECT note.id AS id, snippet(note_fts, -1, :start, :end, '...', 12) AS snippet
            {from_sql}
            ORDER BY bm25(note_fts)
            LIMIT :limit OFFSET :offset
        """),
        {**params, 'start': _SNIPPET_START, 'end': _SNIPPET_END, 'limit': per_page, 'offset': offset},
    ).all()

    note_ids = [row.id for row in rows]
    snippets = {row.id: _snippet_markup(row.snippet) for row in rows}
    notes_by_id = {n.id: n for n in Note.query.filter(Note.id.in_(note_ids)).all()}

    items = []
    for note_id in note_ids:
        note = notes_by_id.get(note_id)
        if note is not None:
            note.snippet = snippets[note_id]
            items.append(note)

    return SimplePagination(items, page, per_page, total)


def keyword_search(user_id, query, category=None, tag=None, source_type=None, page=1, per_page=10):
    if query:
        return _fts_search(user_id, query, category, tag, source_type, page, per_page)

    q = Note.query.filter_by(user_id=user_id, is_archived=False)

    if category:
        q = q.filter_by(category=category)

    if tag:
        q = q.join(Note.tags).filter(Tag.name == tag)

    if source_type:
        q = q.filter_by(source_type=source_type)

    return q.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).paginate(page=page, per_page=per_page)


def semantic_search(user_id, query, category=None, tag=None, source_type=None, page=1, per_page=10, min_similarity=0.5):
    # indexer.ready is set once by the background worker after it loads
    # the model at startup - never here. If it's not ready (still loading,
    # or no network to fetch the model at all), semantic search degrades
    # to "no semantic results" and hybrid_search below falls back to
    # keyword-only, rather than loading the model in this request.
    model = get_ready_model()
    if not query or not indexer.ready or model is None:
        return SimplePagination([], page, per_page, 0)

    query_emb = model.encode(query, convert_to_numpy=True, normalize_embeddings=True)

    all_embeddings = get_all_embeddings(user_id)

    similarities = []
    for note_id, emb in all_embeddings.items():
        sim = cosine_similarity(query_emb, emb)
        if sim >= min_similarity:
            similarities.append((note_id, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)

    if not similarities:
        return SimplePagination([], page, per_page, 0)

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

    # Vector retrieval only runs once the background worker has actually
    # loaded a model - calling semantic_search when it isn't ready would
    # just return empty anyway (see its own guard above), but checking
    # indexer.ready here makes "FTS + vector via RRF only when vectors are
    # ready" an explicit branch instead of an incidental result of that
    # guard, and skips the embedding-table read entirely when it can't
    # contribute anything.
    if indexer.ready:
        semantic_results = semantic_search(user_id, query, category, tag, source_type, page=1, per_page=fetch_depth)
    else:
        semantic_results = SimplePagination([], 1, fetch_depth, 0)

    # Reciprocal Rank Fusion: a standard way to merge two ranked lists
    # without needing their scores to be on the same scale (an FTS5 bm25
    # score and a cosine similarity aren't comparable numbers). k=60 is the
    # standard constant from the RRF literature.
    RRF_K = 60
    combined = {}
    snippets = {}

    for i, note in enumerate(keyword_results.items):
        combined[note.id] = combined.get(note.id, 0) + 1.0 / (RRF_K + i + 1)
        snippet = getattr(note, 'snippet', None)
        if snippet is not None:
            snippets[note.id] = snippet

    for i, note in enumerate(semantic_results.items):
        combined[note.id] = combined.get(note.id, 0) + 1.0 / (RRF_K + i + 1)

    sorted_ids = sorted(combined.keys(), key=lambda x: combined[x], reverse=True)

    notes = Note.query.filter(Note.id.in_(sorted_ids), Note.user_id == user_id).all()
    note_dict = {n.id: n for n in notes}
    sorted_notes = []
    for nid in sorted_ids:
        note = note_dict.get(nid)
        if note is None:
            continue
        if nid in snippets:
            note.snippet = snippets[nid]
        sorted_notes.append(note)

    start = (page - 1) * per_page
    end = start + per_page
    page_items = sorted_notes[start:end]

    return SimplePagination(page_items, page, per_page, len(sorted_notes))
