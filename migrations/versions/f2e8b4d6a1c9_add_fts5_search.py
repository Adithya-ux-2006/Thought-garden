"""Add SQLite FTS5 full-text index for notes, kept in sync by triggers

Revision ID: f2e8b4d6a1c9
Revises: e7a3f9c2d4b1
Create Date: 2026-09-26

"""
from alembic import op


revision = 'f2e8b4d6a1c9'
down_revision = 'e7a3f9c2d4b1'
branch_labels = None
depends_on = None


def upgrade():
    # External-content FTS5 table: the indexed text lives in note.title /
    # note.content, not duplicated here - note_fts only stores the inverted
    # index, keyed by note.id via content_rowid. Not representable as a
    # SQLAlchemy model (it's a virtual table); test_migrations.py's schema
    # diff explicitly excludes note_fts and its shadow tables for this
    # reason.
    op.execute("""
        CREATE VIRTUAL TABLE note_fts USING fts5(
            title, content, content='note', content_rowid='id'
        )
    """)

    # Backfill notes that already exist on databases upgrading from before
    # this revision.
    op.execute("""
        INSERT INTO note_fts(rowid, title, content)
        SELECT id, title, content FROM note
    """)

    # Triggers keep note_fts in sync with note on every INSERT/UPDATE/DELETE,
    # in the same transaction as the write - unlike embeddings (queued for
    # the background indexer), full-text search results are never stale.
    op.execute("""
        CREATE TRIGGER note_fts_ai AFTER INSERT ON note BEGIN
            INSERT INTO note_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
        END
    """)
    op.execute("""
        CREATE TRIGGER note_fts_ad AFTER DELETE ON note BEGIN
            INSERT INTO note_fts(note_fts, rowid, title, content) VALUES ('delete', old.id, old.title, old.content);
        END
    """)
    op.execute("""
        CREATE TRIGGER note_fts_au AFTER UPDATE ON note BEGIN
            INSERT INTO note_fts(note_fts, rowid, title, content) VALUES ('delete', old.id, old.title, old.content);
            INSERT INTO note_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
        END
    """)


def downgrade():
    op.execute('DROP TRIGGER IF EXISTS note_fts_au')
    op.execute('DROP TRIGGER IF EXISTS note_fts_ad')
    op.execute('DROP TRIGGER IF EXISTS note_fts_ai')
    # Dropping the virtual table also drops its shadow tables
    # (note_fts_data, note_fts_idx, note_fts_docsize, note_fts_config).
    op.execute('DROP TABLE IF EXISTS note_fts')
