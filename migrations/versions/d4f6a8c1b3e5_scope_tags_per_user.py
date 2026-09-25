"""Scope tags per user; drop unused Note.summary

Revision ID: d4f6a8c1b3e5
Revises: f2e8b4d6a1c9
Create Date: 2026-09-26

Tags were a single global namespace (tag.name unique across every user, via
ix_tag_name) - two different users typing the same tag name silently shared
one row (tag suggestions, tag-cloud counts, and "other notes with this tag"
all leaked across accounts). This migration scopes Tag per user:

  - adds tag.user_id, backfilled from the tag's existing notes rather than
    a blind default, since pre-migration tag rows may already carry data
  - a tag attached to exactly one user's notes gets that user_id directly
  - a tag with no notes left (orphaned) is deleted - nothing references it
  - a tag shared across more than one user (only possible under the old
    global namespace) is split into one row per user, with note_tags
    repointed to each new row so no note loses its tag
  - replaces the global unique index on tag.name with a per-user exact
    UniqueConstraint plus a case-insensitive backstop index, mirroring
    User's uq_user_email_lower

As with c4d8a2b6e9f1, downgrade does not attempt to re-merge a split tag
back into one global row - if any split happened, re-adding a global
unique index on tag.name would itself fail on the now-duplicate names, so
downgrade is only safe on a database that never had a multi-user tag.

Note.summary is dropped as dead code (confirmed unused anywhere outside
its own column/migration definition; verified empty in the real dev DB).

The UTCDateTime type change (see app/models.py) stores the same naive-UTC
bytes SQLite has always held on disk - only Python-side read/write
behavior changed - so it needs no DDL here.
"""
from alembic import op
import sqlalchemy as sa


revision = 'd4f6a8c1b3e5'
down_revision = 'f2e8b4d6a1c9'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # recreate='never' forces a direct `ALTER TABLE note DROP COLUMN`
    # (native since SQLite 3.35) instead of batch mode's default copy/
    # drop/rename recreate. That default would DROP the original `note`
    # table, and since note_embeddings.note_id and index_job.note_id both
    # have ON DELETE CASCADE pointing at it, SQLite fires those cascades
    # on the implicit delete a DROP TABLE causes - silently destroying
    # every embedding and pending index job. The native ALTER has no such
    # side effect.
    with op.batch_alter_table('note', recreate='never') as batch_op:
        batch_op.drop_column('summary')

    # recreate='never' here too: a plain ADD COLUMN needs no table copy,
    # and note_tags.tag_id -> tag.id (no explicit ON DELETE) would make
    # SQLite refuse the DROP TABLE a default recreate performs, since
    # NO ACTION blocks dropping a parent row that a child still
    # references - the same class of problem as the note/summary column
    # above, just an outright failure here instead of silent data loss.
    with op.batch_alter_table('tag', recreate='never') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))

    # Must happen before the backfill below: splitting a shared tag inserts
    # a second row with the same `name`, which the still-global ix_tag_name
    # unique index would reject.
    op.drop_index('ix_tag_name', table_name='tag')

    tags = conn.execute(sa.text('SELECT id, name, created_at FROM tag')).fetchall()
    for tag_id, name, created_at in tags:
        user_ids = [row[0] for row in conn.execute(sa.text(
            'SELECT DISTINCT n.user_id FROM note_tags nt '
            'JOIN note n ON n.id = nt.note_id WHERE nt.tag_id = :tag_id'
        ), {'tag_id': tag_id}).fetchall()]

        if not user_ids:
            conn.execute(sa.text('DELETE FROM tag WHERE id = :id'), {'id': tag_id})
            continue

        conn.execute(sa.text('UPDATE tag SET user_id = :uid WHERE id = :id'),
                     {'uid': user_ids[0], 'id': tag_id})

        for extra_user_id in user_ids[1:]:
            new_id = conn.execute(sa.text(
                'INSERT INTO tag (user_id, name, created_at) VALUES (:uid, :name, :created_at)'
            ), {'uid': extra_user_id, 'name': name, 'created_at': created_at}).lastrowid
            conn.execute(sa.text(
                'UPDATE note_tags SET tag_id = :new_id '
                'WHERE tag_id = :old_id AND note_id IN ('
                '  SELECT id FROM note WHERE user_id = :uid'
                ')'
            ), {'new_id': new_id, 'old_id': tag_id, 'uid': extra_user_id})

    # Adding a FK/UniqueConstraint isn't a native SQLite ALTER - this batch
    # does a real copy/drop/rename recreate, and note_tags.tag_id still
    # references the original `tag` table's rows, so the drop half needs
    # foreign key checking off. PRAGMA foreign_keys can't change inside an
    # open transaction, hence the autocommit_block.
    with op.get_context().autocommit_block():
        conn.exec_driver_sql('PRAGMA foreign_keys=OFF')
        with op.batch_alter_table('tag') as batch_op:
            batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)
            batch_op.create_foreign_key('fk_tag_user_id_user', 'user', ['user_id'], ['id'])
            batch_op.create_unique_constraint('uq_tag_user_id_name', ['user_id', 'name'])
        conn.exec_driver_sql('PRAGMA foreign_keys=ON')

    op.create_index('ix_tag_user_id', 'tag', ['user_id'])
    op.create_index('uq_tag_user_id_name_lower', 'tag', ['user_id', sa.text('lower(name)')], unique=True)


def downgrade():
    conn = op.get_bind()

    op.drop_index('uq_tag_user_id_name_lower', table_name='tag')
    op.drop_index('ix_tag_user_id', table_name='tag')

    with op.get_context().autocommit_block():
        conn.exec_driver_sql('PRAGMA foreign_keys=OFF')
        with op.batch_alter_table('tag') as batch_op:
            batch_op.drop_constraint('uq_tag_user_id_name', type_='unique')
            batch_op.drop_constraint('fk_tag_user_id_user', type_='foreignkey')
            batch_op.drop_column('user_id')
        conn.exec_driver_sql('PRAGMA foreign_keys=ON')

    # Fails here if any tag name was ever split across users under this
    # revision - see module docstring; that split is not reversible.
    op.create_index('ix_tag_name', 'tag', ['name'], unique=True)

    with op.batch_alter_table('note', recreate='never') as batch_op:
        batch_op.add_column(sa.Column('summary', sa.Text(), nullable=True))
