"""Add plant/leaf grouping to notes (parent_id + part_index)

A multi-part imported document is stored as one "plant" note whose chunk
notes ("leaves") point back at it through parent_id. part_index keeps the
leaves in document order for the "jump between leaves" pager.

parent_id is deliberately a plain indexed column, not a ForeignKey:
see app/models.py Note.parent_id - SQLite can't alter-add a self-FK, and
recreating `note` would fire the ON DELETE CASCADE wiping embeddings (the
d4f6a8 migration guards against exactly that). SQLite doesn't enforce FKs
in this app anyway; the ORM relationship drives joins and delete-orphan.

Revision ID: a7c5e9d3f2b8
Revises: d4f6a8c1b3e5
Create Date: 2026-10-13

"""
from alembic import op
import sqlalchemy as sa


revision = 'a7c5e9d3f2b8'
down_revision = 'd4f6a8c1b3e5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('note', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('note', sa.Column('part_index', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_note_parent_id'), 'note', ['parent_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_note_parent_id'), table_name='note')
    op.drop_column('note', 'part_index')
    op.drop_column('note', 'parent_id')