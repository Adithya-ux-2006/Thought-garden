# Thought Garden — Current Project Inventory

> Rewritten 2026-09-18 against the actual codebase (routes, models, and
> file tree verified directly, not transcribed from memory). The
> previous version of this file was significantly wrong — see
> `docs/SELF_AUDIT.md` and `CLAUDE.md` for how that was discovered.
> Keep this in sync: if you add a route, model field, or template,
> update it here too, or delete the claim rather than let it drift.

## Repository Root

### Application Code (`app/`)
```
app/__init__.py                      - App factory: CSRFProtect, SQLAlchemy, Flask-Login, db.create_all()
app/models.py                        - User, Note, Tag, Relationship, NoteEmbedding
app/forms.py                         - Flask-WTF forms (Register, Login, Profile, Note, Search, DocumentUpload)
app/notes/routes.py                  - Note CRUD, import_document, edit, delete, pin, archive
app/main/routes.py                   - Landing page, dashboard, insights
app/garden/routes.py                 - Knowledge graph data, focus mode, note detail API
app/search/routes.py                 - Hybrid search results, autocomplete suggest API
app/auth/routes.py                   - Login, register, logout, profile
app/services/embedding_service.py    - SentenceTransformer model loading, embedding storage/retrieval
app/services/similarity_service.py   - lightweight + embedding similarity, relationship management
app/services/keyword_service.py      - stopword-filtered keyword extraction, tag suggestions
app/services/search_service.py       - keyword_search, semantic_search, hybrid_search (RRF-merged)
app/services/document_service.py     - PDF/TXT/MD extraction, chunking, note creation
app/services/pagination.py           - SimplePagination (shared by semantic/hybrid search)
app/services/onboarding_service.py   - starter-garden seeding for new users
app/services/__init__.py             - re-exports of the above (not exhaustive - some callers import directly)
```
There is no `config.py` — config lives entirely in `create_app()` in `app/__init__.py`, reading from environment variables with inline defaults.

### Templates (`app/templates/`)
```
templates/base.html                  - Main layout, navbar, dark mode toggle
templates/main/landing.html          - Public landing page
templates/main/dashboard.html        - Authenticated dashboard
templates/main/insights.html         - Learning insights page
templates/auth/login.html            - Login form
templates/auth/register.html         - Registration form
templates/auth/profile.html          - User profile
templates/notes/list.html            - Notes list with filters (NOT notes/index.html)
templates/notes/create.html          - Create note form + document import
templates/notes/edit.html            - Edit note form + delete
templates/notes/view.html            - View note with connections panel
templates/garden/index.html          - Knowledge graph page with vis-network
templates/search/search.html         - Search form + results (NOT search/index.html)
```

### Static Assets (`app/static/`)
```
static/css/style.css                 - CSS custom properties, responsive design, dark mode
static/js/main.js                    - vis-network graph rendering, search, filters, physics toggle
```

### Root files
```
requirements.txt                     - Python dependencies
seed.py                              - Demo data generator
run.py                               - Application entry point (auto-seed, backfill relationships)
```

---

## Routes (21 endpoints, verified via `app.url_map`)

### Authentication (`app/auth/routes.py`)
| Method | Path | Endpoint |
|--------|------|---------|
| GET/POST | `/auth/login` | `auth.login` |
| GET/POST | `/auth/register` | `auth.register` |
| GET | `/auth/logout` | `auth.logout` |
| GET/POST | `/auth/profile` | `auth.profile` |

### Notes (`app/notes/routes.py`)
| Method | Path | Endpoint |
|--------|------|---------|
| GET | `/notes/` | `notes.list_notes` |
| GET/POST | `/notes/create` | `notes.create` |
| GET | `/notes/<id>` | `notes.view` |
| GET/POST | `/notes/<id>/edit` | `notes.edit` |
| POST | `/notes/<id>/delete` | `notes.delete` |
| POST | `/notes/<id>/pin` | `notes.pin` |
| POST | `/notes/<id>/archive` | `notes.archive` |
| POST | `/notes/import` | `notes.import_document` |
| GET | `/notes/archived` | `notes.archived` (redirects to `list_notes?archived=1`) |

### Garden (`app/garden/routes.py`)
| Method | Path | Endpoint |
|--------|------|---------|
| GET | `/garden/` | `garden.index` |
| GET | `/garden/data` | `garden.data` (JSON for vis-network) |
| GET | `/garden/note/<id>` | `garden.note_detail` (JSON) |
| GET | `/garden/focus/<id>` | `garden.focus` (JSON, depth-limited subgraph) |

### Search (`app/search/routes.py`)
| Method | Path | Endpoint |
|--------|------|---------|
| GET/POST | `/search/` | `search.search` |
| GET | `/search/api/suggest` | `search.suggest` (autocomplete JSON) |

### Main (`app/main/routes.py`)
| Method | Path | Endpoint |
|--------|------|---------|
| GET | `/` | `main.index` |
| GET | `/dashboard` | `main.dashboard` |
| GET | `/insights` | `main.insights` |

---

## Database Tables (5, all real SQLAlchemy models — see `app/models.py`)

### user
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | VARCHAR(100) | Not null |
| email | VARCHAR(120) UNIQUE, indexed | Not null |
| password_hash | VARCHAR(255) | Werkzeug hash, not plaintext |
| created_at | DATETIME | Default utcnow |

### note
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | INTEGER FK → user.id, indexed | Not null |
| title | VARCHAR(200) | Not null |
| content | TEXT | Not null |
| summary | TEXT | Nullable, currently unused by any route |
| category | VARCHAR(50) | Nullable, no index (despite prior docs claiming one) |
| source_type | VARCHAR(20) | Default `'manual'`; also `pdf`/`txt`/`md`/`starter` |
| source_filename | VARCHAR(255) | Nullable |
| is_pinned | BOOLEAN | Default False |
| is_archived | BOOLEAN | Default False |
| created_at | DATETIME, indexed | Default utcnow |
| updated_at | DATETIME | Default/onupdate utcnow |

### tag
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | VARCHAR(50) UNIQUE, indexed | Not null |

### note_tags (association table, no model class)
| Column | Type | Notes |
|--------|------|-------|
| note_id | INTEGER FK → note.id | Composite PK |
| tag_id | INTEGER FK → tag.id | Composite PK |

### relationship
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| source_note_id | INTEGER FK → note.id, indexed | Not null |
| target_note_id | INTEGER FK → note.id, indexed | Not null |
| similarity_score | FLOAT | Not null, 0.0–1.0 |
| relationship_type | VARCHAR(20) | Default `'semantic'` |
| created_at | DATETIME | Default utcnow |
| updated_at | DATETIME | Default/onupdate utcnow |

Constraints: `UNIQUE(source_note_id, target_note_id)`, `CHECK(source_note_id != target_note_id)`.
Field names are `source_note_id`/`target_note_id` — **not** `note1_id`/`note2_id` as earlier docs claimed.

### note_embeddings (`NoteEmbedding` model)
| Column | Type | Notes |
|--------|------|-------|
| note_id | INTEGER PK, FK → note.id (CASCADE) | |
| embedding | BLOB | Raw `float32.tobytes()`, **not** pickle (pickle rows from before this change still decode via a fallback) |
| updated_at | DATETIME | Default/onupdate utcnow |

No `model_name` column exists — the model name is an env var (`EMBEDDING_MODEL`), not stored per-row. There is no `embedding_generated` column on `note` either; embedding presence is determined by whether a `note_embeddings` row exists.

---

## Services

### embedding_service.py
- Lazy-loads `sentence-transformers` model (`all-MiniLM-L6-v2` by default, `EMBEDDING_MODEL` env override)
- `generate_embedding(note)` — encodes title+content+tags+category, stores as raw bytes via the `NoteEmbedding` model
- `get_embedding(note_id, generate_if_missing=...)` — in-process cache, falls back to DB, optionally generates
- `get_all_embeddings(user_id, generate_if_missing=...)` — bulk fetch for a user's notes
- `invalidate_embedding_cache(note_id)` — drops one note's cached vector (called on delete)

### similarity_service.py
- `lightweight_similarity()` — keyword/tag/category overlap scorer, no ML model needed
- `update_relationships_for_note()` — uses real embeddings if already generated, otherwise the lightweight scorer; never triggers model download inline
- `SIMILARITY_THRESHOLD` (embedding-based, default 0.45), `KEYWORD_THRESHOLD` (lightweight, default 0.18), `MAX_RELATED_NOTES` (default 5) — all env-overridable
- `ensure_all_relationships()` — startup backfill across all users

### keyword_service.py
- `extract_keywords()` — regex word split, stopword filter, frequency ranking (not TF-IDF)
- `suggest_tags()` — matches keywords against existing user tags + related notes' tags

### search_service.py
- `keyword_search()` — `ILIKE` substring match on title/content (not SQLite FTS5, despite README wording)
- `semantic_search()` — cosine similarity against embeddings, blocks on model load if none generated yet
- `hybrid_search()` — merges the two via Reciprocal Rank Fusion (`1/(60+rank)`)

### document_service.py
- PDF extraction via PyPDF2, plain read for TXT/MD (UTF-8 with latin-1 fallback)
- `chunk_text()` — splits long documents on sentence/paragraph boundaries with overlap
- `create_notes_from_document()` — creates one note per chunk, runs relationship scoring per note

---

## Seed Data (`seed.py`)

17 notes across 5 categories for the demo/starter garden — see `seed.py` directly for exact titles and content; don't trust a stale count here if `seed.py` has changed since this was last verified.

### Demo Account
- Email: `demo@thoughtgarden.app`
- Password: `demo1234`
