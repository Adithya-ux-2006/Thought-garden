"""Normalize user emails and enforce case-insensitive uniqueness

Revision ID: b3c9e1f2a7d4
Revises: a1b2c3d4e5f6
Create Date: 2026-09-24

"""
from alembic import op
import sqlalchemy as sa


revision = 'b3c9e1f2a7d4'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # Check before changing anything: SQLite DDL here is not transactional,
    # so refusing must happen while the data is still untouched.
    collisions = conn.execute(sa.text(
        'SELECT lower(trim(email)) FROM "user" GROUP BY lower(trim(email)) HAVING COUNT(*) > 1'
    )).fetchall()
    if collisions:
        raise RuntimeError(
            f'{len(collisions)} email address(es) differ only by case or whitespace. '
            'Merge or rename those accounts, then run the upgrade again.'
        )
    conn.execute(sa.text('UPDATE "user" SET email = lower(trim(email))'))
    op.create_index('uq_user_email_lower', 'user', [sa.text('lower(email)')], unique=True)


def downgrade():
    # Lower-cased emails are left as they are; they remain valid.
    op.drop_index('uq_user_email_lower', table_name='user')
