"""Add background indexer: index_job queue, content-hash tracking, method-aware relationships

Revision ID: e7a3f9c2d4b1
Revises: c4d8a2b6e9f1
Create Date: 2026-09-25

"""
from alembic import op
import sqlalchemy as sa


revision = 'e7a3f9c2d4b1'
down_revision = 'c4d8a2b6e9f1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'index_job',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('note_id', sa.Integer(), sa.ForeignKey('note.id', ondelete='CASCADE'),
                  nullable=False, unique=True, index=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    with op.batch_alter_table('note_embeddings') as batch_op:
        batch_op.add_column(sa.Column('content_hash', sa.String(length=64), nullable=True))

    with op.batch_alter_table('relationship') as batch_op:
        batch_op.add_column(sa.Column('method', sa.String(length=20), nullable=False,
                                       server_default='embedding'))


def downgrade():
    with op.batch_alter_table('relationship') as batch_op:
        batch_op.drop_column('method')

    with op.batch_alter_table('note_embeddings') as batch_op:
        batch_op.drop_column('content_hash')

    op.drop_table('index_job')
