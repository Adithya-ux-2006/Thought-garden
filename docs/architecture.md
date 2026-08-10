# Thought Garden Architecture

## Overview

Thought Garden follows a modular Flask application architecture with clear separation of concerns. The design prioritizes simplicity, maintainability, and extensibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Landing │  │Dashboard│  │  Notes  │  │ Garden  │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                         │                                   │
│                    Jinja2 + Bootstrap 5 + vis-network       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Flask Blueprints                        │
│  ┌─────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌─────┐          │
│  │Auth │  │Notes │  │Garden│  │Search│  │Main │          │
│  └─────┘  └──────┘  └──────┘  └──────┘  └─────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐              │
│  │ Embedding │  │Similarity │  │  Search   │              │
│  │  Service  │  │  Service  │  │  Service  │              │
│  └───────────┘  └───────────┘  └───────────┘              │
│  ┌───────────┐  ┌───────────┐                              │
│  │ Keyword   │  │ Document  │                              │
│  │  Service  │  │  Service  │                              │
│  └───────────┘  └───────────┘                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy ORM                          │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────┐  ┌──────┐  ┌───────┐  ┌──────────────┐      │
│  │  User   │  │ Note │  │  Tag  │  │ Relationship │      │
│  └─────────┘  └──────┘  └───────┘  └──────────────┘      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   SQLite                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI/ML Layer                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          sentence-transformers (MiniLM)             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               scikit-learn (cosine)                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

```
┌──────────────┐       ┌──────────────┐
│    User      │       │     Tag      │
├──────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)      │
│ name         │       │ name         │
│ email (UQ)   │       │ created_at   │
│ password_hash│       └──────────────┘
│ created_at   │              │
└──────────────┘              │
       │                      │
       │ 1:N                  │ M:N
       ▼                      ▼
┌──────────────┐       ┌──────────────┐
│    Note      │◄──────│  note_tags   │
├──────────────┤       ├──────────────┤
│ id (PK)      │       │ note_id (FK) │
│ user_id (FK) │       │ tag_id (FK)  │
│ title        │       └──────────────┘
│ content      │
│ summary      │       ┌──────────────┐
│ category     │       │ Relationship │
│ source_type  │       ├──────────────┤
│ source_file  │       │ id (PK)      │
│ is_pinned    │       │ source_id(FK)│
│ is_archived  │       │ target_id(FK)│
│ created_at   │       │ similarity   │
│ updated_at   │       │ rel_type     │
└──────────────┘       │ created_at   │
                       │ updated_at   │
                       └──────────────┘
```

## Key Design Decisions

### 1. Application Factory Pattern
- Enables testing with different configurations
- Supports multiple instances
- Clear initialization flow

### 2. Blueprint Organization
- **auth:** Authentication and authorization
- **notes:** CRUD operations for knowledge entries
- **garden:** Knowledge graph visualization
- **search:** Hybrid search functionality
- **main:** Dashboard and landing page

### 3. Service Layer
- Business logic separated from routes
- Services are replaceable for future upgrades
- Clear interfaces between components

### 4. Embedding Storage
- Embeddings stored as binary blobs in SQLite
- Service layer abstracts storage details
- Migration path to pgvector available

### 5. Relationship Management
- Many-to-many with similarity scores
- Unique constraint prevents duplicates
- Check constraint prevents self-relationships

## Data Flow

### Note Creation
```
User submits form
    ↓
Validate input
    ↓
Create Note record
    ↓
Process tags (create if needed)
    ↓
Generate embedding (SentenceTransformer)
    ↓
Store embedding
    ↓
Compare with existing embeddings
    ↓
Calculate cosine similarities
    ↓
Create Relationship records
    ↓
Generate explanations
    ↓
Return to user
```

### Search
```
User enters query
    ↓
Parse query type (keyword/semantic)
    ↓
Execute keyword search (SQLite)
    ↓
Execute semantic search (embeddings)
    ↓
Merge results
    ↓
Rank by combined score
    ↓
Return paginated results
```

## Extension Points

### EmbeddingService
- Current: SentenceTransformer (local)
- Future: OpenAI, Cohere, custom models

### SearchService
- Current: SQLite + local vectors
- Future: PostgreSQL + pgvector

### ExplanationService
- Current: Keyword overlap
- Future: LLM-generated

### Storage
- Current: Local filesystem
- Future: Cloud storage (S3, GCS)

## Security Considerations

- Passwords hashed with Werkzeug (SHA-256)
- Session-based authentication
- CSRF protection on forms (Flask-WTF CSRFProtect initialized)
- User ownership validation on all note mutations
- File upload validation with secure_filename
- SQL injection prevention via ORM
- XSS prevention via Jinja2 auto-escaping (removed `| safe` filter)

## Performance Optimizations

- Embedding caching in memory
- Lazy model loading
- Pagination for large lists
- Relationship threshold filtering (0.45 default)
- Database indexing on foreign keys

## Known Issues

- `note_embeddings` table created via raw SQL, not SQLAlchemy model (see `__init__.py`)
- Category filter checkboxes in garden template have no JavaScript logic
- Duplicate `cosine_similarity` function in similarity_service.py and search_service.py
- Duplicate `extract_keywords` in similarity_service.py and keyword_service.py
- Duplicate `Pagination` class in search_service.py