"""Initial schema baseline

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-09-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # user
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # note
    op.create_table(
        'note',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False, index=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('source_type', sa.String(length=20), server_default='manual'),
        sa.Column('source_filename', sa.String(length=255), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), server_default='0'),
        sa.Column('is_archived', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # tag
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=50), unique=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # note_tags (association table)
    op.create_table(
        'note_tags',
        sa.Column('note_id', sa.Integer(), sa.ForeignKey('note.id'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tag.id'), primary_key=True),
    )

    # note_embeddings
    op.create_table(
        'note_embeddings',
        sa.Column('note_id', sa.Integer(), sa.ForeignKey('note.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('embedding', sa.LargeBinary(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # relationship
    op.create_table(
        'relationship',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_note_id', sa.Integer(), sa.ForeignKey('note.id'), nullable=False, index=True),
        sa.Column('target_note_id', sa.Integer(), sa.ForeignKey('note.id'), nullable=False, index=True),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('relationship_type', sa.String(length=20), server_default='semantic'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('source_note_id', 'target_note_id', name='unique_relationship'),
        sa.CheckConstraint('source_note_id != target_note_id', name='no_self_relationship'),
    )


def downgrade():
    op.drop_table('relationship')
    op.drop_table('note_embeddings')
    op.drop_table('note_tags')
    op.drop_table('tag')
    op.drop_table('note')
    op.drop_table('user')
