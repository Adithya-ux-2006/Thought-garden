# Database Schema - Thought Garden

## Overview

Thought Garden uses SQLite with SQLAlchemy ORM. The schema is designed for simplicity while supporting future migration to PostgreSQL.

## Tables

### User

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | NOT NULL | User's display name |
| email | VARCHAR(120) | UNIQUE, NOT NULL | Login email |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| created_at | DATETIME | DEFAULT NOW | Account creation time |

### Note

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| user_id | INTEGER | FOREIGN KEY, INDEX | Owner's user ID |
| title | VARCHAR(200) | NOT NULL | Note title |
| content | TEXT | NOT NULL | Note body text |
| summary | TEXT | NULLABLE | Auto-generated summary |
| category | VARCHAR(50) | NULLABLE, INDEX | Topic category |
| source_type | VARCHAR(20) | DEFAULT 'manual' | manual/pdf/markdown/text |
| source_filename | VARCHAR(255) | NULLABLE | Original filename |
| is_pinned | BOOLEAN | DEFAULT FALSE | Pinned to top |
| is_archived | BOOLEAN | DEFAULT FALSE | Soft delete |
| created_at | DATETIME | DEFAULT NOW, INDEX | Creation time |
| updated_at | DATETIME | DEFAULT NOW | Last modification |

### Tag

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| name | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Tag name |
| created_at | DATETIME | DEFAULT NOW | Creation time |

### note_tags (Association)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| note_id | INTEGER | FOREIGN KEY, PK | Note ID |
| tag_id | INTEGER | FOREIGN KEY, PK | Tag ID |

### Relationship

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| source_note_id | INTEGER | FOREIGN KEY, INDEX | Source note ID |
| target_note_id | INTEGER | FOREIGN KEY, INDEX | Target note ID |
| similarity_score | FLOAT | NOT NULL | 0.0 to 1.0 |
| relationship_type | VARCHAR(20) | DEFAULT 'semantic' | Relationship type |
| created_at | DATETIME | DEFAULT NOW | Creation time |
| updated_at | DATETIME | DEFAULT NOW | Last update |

**Constraints:**
- UNIQUE(source_note_id, target_note_id)
- CHECK(source_note_id != target_note_id)

### note_embeddings (Virtual Table)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| note_id | INTEGER | PRIMARY KEY | Note ID |
| embedding | BLOB | NOT NULL | Pickled numpy array |
| updated_at | DATETIME | DEFAULT NOW | Last update |

## Relationships

```
User 1 ──── N Note
Note M ──── M Tag (via note_tags)
Note 1 ──── N Relationship (as source)
Note 1 ──── N Relationship (as target)
```

## Indexes

- `ix_user_email`: User.email
- `ix_note_user_id`: Note.user_id
- `ix_note_category`: Note.category
- `ix_note_created_at`: Note.created_at
- `ix_tag_name`: Tag.name
- `ix_relationship_source`: Relationship.source_note_id
- `ix_relationship_target`: Relationship.target_note_id

## Migration Notes

### SQLite to PostgreSQL

When migrating:
1. Replace `BLOB` with `BYTEA` for embeddings
2. Use `pgvector` extension for vector storage
3. Replace `DATETIME` with `TIMESTAMP`
4. Update `AUTOINCREMENT` syntax
5. Consider partitioning for large datasets

### Embedding Storage

Current implementation stores embeddings as pickled numpy arrays. Future options:
- pgvector (PostgreSQL)
- Pinecone (cloud vector DB)
- Weaviate (self-hosted vector DB)