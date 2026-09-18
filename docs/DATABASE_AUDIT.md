# Thought Garden — Database Audit

> Rewritten 2026-09-18 against `app/models.py` directly — the previous
> version had wrong column names, a nonexistent column, and several
> "not implemented" claims that were actually already handled in code.
> The Relationship Quality Audit and Threshold Analysis sections below
> are numbers from a one-off analysis against a fully-embedded demo
> garden and are kept as historical reference — see the caveat at the
> end of that section before trusting them for the app's actual
> day-to-day behavior.

## Schema Audit (verified against `app/models.py`)

### note table
No `embedding_generated` column exists. Whether a note has an embedding is determined by whether a matching row exists in `note_embeddings` — there's nothing to audit here, the earlier claim was simply wrong.

**Real, still-open issue:** `note.category` has **no index** (`db.Column(db.String(50), nullable=True)`, no `index=True`), despite this file previously claiming it was indexed. Every category filter (`garden/index.html`, `search`, dashboard stats) does a full scan on this column. Worth adding `index=True` if category filtering becomes a bottleneck at scale — low priority at current demo data volumes.

### note_embeddings table (`NoteEmbedding` model)
**Previously:** created via raw SQL in `__init__.py`, not a SQLAlchemy model — couldn't use `db.create_all()`, no ORM-level cascade.
**Now fixed:** `NoteEmbedding` is a real model (see `app/models.py`), created via `db.create_all()` like every other table. `Note.embedding_row` declares `cascade='all, delete-orphan'` so deleting a note deletes its embedding row through the ORM — this does not depend on SQLite's `PRAGMA foreign_keys=ON` (which SQLAlchemy does not enable by default), so it works correctly regardless of that pragma's state.

### relationship table
Actual column names are **`source_note_id`** and **`target_note_id`** — not `note1_id`/`note2_id` as this file previously said.

Constraints actually present:
- `UniqueConstraint('source_note_id', 'target_note_id')` — prevents an exact duplicate pair in one direction. Does **not** by itself prevent both an A→B row and a separate B→A row from existing (the app's own logic in `similarity_service.py` avoids creating both by always checking `tuple(sorted(...))` before inserting, but nothing at the DB level enforces that).
- `CheckConstraint('source_note_id != target_note_id', name='no_self_relationship')` — **this already exists.** A prior version of this doc recommended adding it as future work; it's done.

### tags / note_tags tables
Still genuinely underused: `keyword_service.suggest_tags()` computes tag suggestions but nothing in the note create/edit flow surfaces or auto-applies them — tags are entirely manual (whatever the user types in the tags field). Not a bug, just an unrealized feature; seed data (`seed.py`) may or may not populate tags depending on what's in it currently — check directly rather than trusting a row count here.

## Cascade Behavior (verified against `app/models.py`, not assumed)

| On deleting... | What cascades | Mechanism |
|---|---|---|
| A `User` | Their `Note`s | `User.notes` relationship, `cascade='all, delete-orphan'` |
| A `Note` | Its `Tag` associations | `note_tags` association table rows removed automatically (many-to-many) |
| A `Note` | `Relationship` rows referencing it (either direction) | `Note.relationships` / `Note.inverse_relationships`, both `cascade='all, delete-orphan'` — **this already works**, a prior version of this doc incorrectly flagged it as not implemented |
| A `Note` | Its `NoteEmbedding` row | `Note.embedding_row`, `cascade='all, delete-orphan'` (added alongside the model itself) |

All of the above are ORM-level cascades (SQLAlchemy issues the DELETE statements itself), which is why they work regardless of whether SQLite's own foreign-key pragma is enabled for a given connection.

## Indexes (verified against `app/models.py`)

| Column | Indexed? |
|---|---|
| `note.user_id` | ✅ `index=True` |
| `note.category` | ❌ not indexed (see above) |
| `note.created_at` | ✅ `index=True` |
| `relationship.source_note_id` | ✅ `index=True` |
| `relationship.target_note_id` | ✅ `index=True` |
| `note_embeddings.note_id` | ✅ primary key |
| `user.email` | ✅ `index=True` (also unique) |
| `tag.name` | ✅ `index=True` (also unique) |

## Relationship Quality Audit (historical — from a prior analysis run)

The table below is preserved from an earlier one-off analysis of the demo seed garden (17 notes, all fully embedded) at `SIMILARITY_THRESHOLD=0.45`. **Caveat:** these numbers reflect embedding-based semantic scores on a garden where every note already had a generated embedding. In normal day-to-day use, `update_relationships_for_note()` only uses real embeddings if they've already been generated for both notes being compared — otherwise it falls back to the lightweight keyword/tag/category scorer (`lightweight_similarity()`), which produces different scores against a different threshold (`KEYWORD_SIMILARITY_THRESHOLD`, default 0.18). Since notes now get their embeddings generated automatically shortly after save (background indexing), a freshly-created garden should converge to something close to this table after a short delay — but don't treat these exact percentages as guaranteed without re-running the analysis.

| Note 1 | Note 2 | Similarity | Assessment |
|--------|--------|-----------|----------|
| ML Fundamentals | Deep Learning | 0.557 | Reasonable — ML is foundation of DL |
| ML Fundamentals | Data Science | 0.571 | Reasonable — ML is core of DS |
| ML Fundamentals | Computer Vision | 0.538 | Reasonable — CV uses ML |
| ML Fundamentals | Neural Networks | 0.514 | Reasonable — NN is an ML technique |
| ML Fundamentals | Adaptive Threats | 0.516 | Weak — cross-domain AI↔Cyber, borderline |
| Neural Networks | Deep Learning | 0.719 | Strong — DL is deep NN |
| Neural Networks | Computer Vision | 0.536 | Reasonable — CV uses NN |
| Deep Learning | NLP | 0.505 | Reasonable — DL powers modern NLP |
| Deep Learning | Computer Vision | 0.635 | Reasonable — DL is used in CV |
| NLP | Transformer Paper | 0.573 | Reasonable — Transformers are an NLP architecture |
| IDS | Network Security | 0.507 | Reasonable — IDS is a network security tool |
| IDS | Adaptive Threats | 0.512 | Reasonable — both cybersecurity defense |
| Network Security | Adaptive Threats | 0.505 | Reasonable — both cybersecurity defense |
| Process Management | Deadlock | 0.566 | Reasonable — deadlock is a process-mgmt problem |
| CPU Scheduling | Process Management | 0.567 | Reasonable — scheduling is process mgmt |
| Agile | Requirements | 0.599 | Reasonable — both SE practices |
| Agile | Testing | 0.538 | Reasonable — both SE practices |

16/17 pairs judged as reasonable connections; one (ML Fundamentals ↔ Adaptive Threats) is a weaker cross-domain link near the threshold.

### Threshold sweep (same historical run)
| Threshold | Relationships found |
|-----------|--------------------|
| 0.70 | 2 — too restrictive, this was the original broken default (see `docs/SELF_AUDIT.md`) |
| 0.55 | 15 |
| 0.45 | 25 (current default) |
| 0.40 | 35+ — noisier, more marginal pairs |

## Open Recommendations (as of 2026-09-18)

1. ~~Create `NoteEmbedding` SQLAlchemy model~~ — **done**.
2. ~~Add cascade for relationships referencing notes~~ — **already existed**, prior doc version was wrong about this.
3. ~~Add `source_note_id != target_note_id` check constraint~~ — **already existed**.
4. ~~Remove `embedding_generated` column~~ — **never existed**, prior doc was wrong.
5. Consider indexing `note.category` if filtering becomes slow at scale.
6. Decide whether tag suggestions (`keyword_service.suggest_tags()`) should auto-apply or stay a manual-only feature — currently computed but unused by any route.
7. No migration tooling (Alembic or equivalent) exists — any future schema change currently means deleting and recreating the SQLite file. Worth addressing before this app has any real user data worth preserving across schema changes.
