# Thought Garden — Current Project Inventory

## Repository Root (`D:\thoughtgarden\`)

### Application Code (`app/`)
```
app/__init__.py          - App factory, CSRFProtect, note_embeddings SQL
app/models.py            - User, Note, Tag, Relationship models
app/forms.py             - Flask-WTF forms (Register, Login, Profile, Note, Search, DocumentUpload)
app/notes/routes.py      - Note CRUD, import_document, edit, delete, pin, archive
app/main/routes.py       - Landing page, dashboard, insights, user_profile
app/garden/routes.py     - Knowledge graph data, focus mode, note detail API
app/search/routes.py     - Search results with hybrid search
app/auth/routes.py       - Login, register, logout, profile
app/services/embedding_service.py   - SentenceTransformer model loading, embedding generation
app/services/similarity_service.py  - cosine_similarity, relationship management
app/services/keyword_service.py     - TF-IDF keyword extraction, tag suggestions
app/services/search_service.py      - keyword_search, semantic_search, hybrid_search
app/services/document_service.py    - PDF/TXT/MD extraction, chunking, note creation
app/services/__init__.py            - Re-exports (shadowing warnings)
```

### Templates (`app/templates/`)
```
templates/base.html                    - Main layout, navbar, dark mode toggle
templates/landing.html                 - Public landing page
templates/dashboard.html               - Authenticated dashboard
templates/insights.html                - Learning insights page
templates/auth/login.html              - Login form
templates/auth/register.html           - Registration form
templates/auth/profile.html            - User profile
templates/notes/index.html             - Notes list with filters
templates/notes/create.html            - Create note form
templates/notes/edit.html              - Edit note form
templates/notes/view.html              - View note with connections panel
templates/garden/index.html            - Knowledge graph page with vis-network
templates/search/index.html            - Search results
```

### Static Assets (`app/static/`)
```
static/css/style.css                   - CSS custom properties, responsive design
static/js/main.js                      - vis-network graph, search, physics toggle
```

### Configuration
```
config.py                  - Config classes (base, dev, production)
requirements.txt           - Python dependencies
seed.py                    - Demo data generator
run.py                     - Application entry point
```

---

## Routes (12 Endpoints)

### Authentication
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET/POST | `/auth/login` | `login()` | User login |
| GET/POST | `/auth/register` | `register()` | New user registration |
| GET | `/auth/logout` | `logout()` | User logout |
| GET/POST | `/auth/profile` | `profile()` | User profile (login required) |

### Notes
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/notes/` | `notes()` | List all notes (login required) |
| GET/POST | `/notes/create` | `create_note()` | Create new note (login required) |
| GET | `/notes/<id>` | `note_detail()` | View note with connections |
| GET/POST | `/notes/<id>/edit` | `edit_note()` | Edit note (owner only) |
| POST | `/notes/<id>/delete` | `delete_note()` | Delete note (owner only) |
| POST | `/notes/<id>/pin` | `pin_note()` | Toggle pin (owner only) |
| POST | `/notes/<id>/archive` | `archive_note()` | Toggle archive (owner only) |
| POST | `/notes/import` | `import_document()` | Import PDF/TXT/MD (login required) |

### Garden
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/garden/` | `garden()` | Knowledge graph page |
| GET | `/garden/data` | `garden_data()` | JSON API for vis-network |
| GET | `/garden/note/<id>` | `garden_note_detail()` | Note detail for garden |
| GET | `/garden/focus/<id>` | `focus_mode()` | Focus mode centered on note |

### Search
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/search/` | `search()` | Hybrid search results |

### Main
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/` | `landing()` | Public landing page |
| GET | `/dashboard` | `dashboard()` | User dashboard (login required) |
| GET | `/insights` | `insights()` | Learning insights (login required) |

---

## Database Tables (6)

### users
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| username | VARCHAR(80) UNIQUE | Not null |
| email | VARCHAR(120) UNIQUE | Not null |
| password_hash | VARCHAR(128) | Not null |
| bio | TEXT | Optional |
| avatar_url | VARCHAR(200) | Optional |
| created_at | DATETIME | Default now |
| last_login | DATETIME | Nullable |

### notes
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| title | VARCHAR(200) | Not null |
| content | TEXT | Not null |
| user_id | INTEGER FK | References users.id |
| category | VARCHAR(50) | Default 'General' |
| source_type | VARCHAR(20) | Default 'manual' |
| source_url | VARCHAR(500) | Optional |
| is_pinned | BOOLEAN | Default false |
| is_archived | BOOLEAN | Default false |
| embedding_generated | BOOLEAN | Default false |
| created_at | DATETIME | Default now |
| updated_at | DATETIME | Auto-update |

### tags
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| name | VARCHAR(50) UNIQUE | Not null |

### note_tags (association)
| Column | Type | Notes |
|--------|------|-------|
| note_id | INTEGER FK | References notes.id |
| tag_id | INTEGER FK | References tags.id |
| PK | (note_id, tag_id) | Composite |

### relationships
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| note1_id | INTEGER FK | References notes.id |
| note2_id | INTEGER FK | References notes.id |
| similarity | FLOAT | 0.0-1.0 |
| relationship_type | VARCHAR(50) | 'related' |
| created_at | DATETIME | Default now |
| UNIQUE | (note1_id, note2_id) | Prevents duplicates |

### note_embeddings
| Column | Type | Notes |
|--------|------|-------|
| note_id | INTEGER PK | References notes.id |
| embedding | BLOB | Pickled numpy array |
| model_name | VARCHAR(100) | Default 'all-MiniLM-L6-v2' |
| created_at | DATETIME | Default now |
*Note: Created via raw SQL in __init__.py, not SQLAlchemy model*

---

## Services

### EmbeddingService
- Loads sentence-transformers model (all-MiniLM-L6-v2)
- Generates embeddings from text
- Stores/loads embeddings from note_embeddings table
- Batch processing for multiple texts

### SimilarityService
- cosine_similarity between embeddings
- Threshold: 0.45 (default)
- find_related_notes: returns notes above threshold
- manage_relationships: creates/updates Relationship records
- Batch find: O(n²) pairwise comparison

### KeywordService
- TF-IDF keyword extraction
- Tag suggestions from note content
- TF-IDF document similarity

### SearchService
- keyword_search: LIKE queries with ranking
- semantic_search: cosine similarity against all embeddings
- hybrid_search: weighted combination (keyword 0.4 + semantic 0.6)
- Pagination via custom class

### DocumentService
- PDF extraction via PyPDF2
- TXT and Markdown reading
- Automatic title/category detection
- Text chunking for long documents
- Note creation + embedding generation

---

## Seed Data

### Notes by Category
| Category | Count | Notes |
|----------|-------|-------|
| AI | 6 | ML Fundamentals, Neural Networks, Deep Learning, NLP, Computer Vision, Data Science |
| Cybersecurity | 3 | IDS, Network Security, Adaptive Threats |
| Software Engineering | 3 | Agile, Requirements, Testing |
| Operating Systems | 3 | CPU Scheduling, Process Management, Deadlock |
| Research | 2 | Adaptive Cybersecurity paper, Transformer Architecture paper |
| **Total** | **17** | |

### Relationships Discovered (25+ at threshold 0.45)
- ML Fundamentals → Deep Learning (56%), Data Science (57%), Computer Vision (54%), Neural Networks (51%), Adaptive Threats (52%)
- Neural Networks → Deep Learning (72%)
- IDS → Network Security (51%), Adaptive Threats (51%)
- Process Management → Deadlock (57%)
- CPU Scheduling → Process Management (57%)

### Demo Account
- Email: demo@thoughtgarden.app
- Password: demo1234
