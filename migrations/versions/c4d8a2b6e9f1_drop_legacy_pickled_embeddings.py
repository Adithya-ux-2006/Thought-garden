"""Delete legacy pickled embeddings

Revision ID: c4d8a2b6e9f1
Revises: b3c9e1f2a7d4
Create Date: 2026-09-24

Embeddings are derived data; deleted rows are regenerated on demand as raw
float32 bytes, so the app never needs to unpickle database content.
"""
from alembic import op
import sqlalchemy as sa


revision = 'c4d8a2b6e9f1'
down_revision = 'b3c9e1f2a7d4'
branch_labels = None
depends_on = None


def upgrade():
    # Same signature as embedding_service._looks_like_pickle: protocol 2-5
    # header (0x80, version) and trailing STOP opcode '.'.
    op.get_bind().execute(sa.text(
        "DELETE FROM note_embeddings "
        "WHERE substr(embedding, 1, 1) = X'80' "
        "AND substr(embedding, 2, 1) IN (X'02', X'03', X'04', X'05') "
        "AND substr(embedding, -1, 1) = X'2E'"
    ))


def downgrade():
    # Deleted rows are regenerated on demand; nothing to restore.
    pass
