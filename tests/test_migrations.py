import os

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect

from app import create_app, db

MIGRATIONS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations'))
BASELINE = 'a1b2c3d4e5f6'


def _file_app(tmp_path, name='migrate.db'):
    return create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{(tmp_path / name).as_posix()}',
        'SECRET_KEY': 'test-secret-key',
    })


def _is_ignored_table(name):
    # alembic_version has no model; note_fts is a virtual FTS5 table (plus
    # its note_fts_data/idx/docsize/config shadow tables) with no
    # SQLAlchemy-representable schema - both are expected to exist in the
    # database without a matching model.
    return name == 'alembic_version' or name == 'note_fts' or name.startswith('note_fts_')


def _schema_diff():
    with db.engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), db.metadata)
        # compare_metadata can't reflect SQLite expression indexes, so check
        # every model-declared index exists by name as well.
        db_indexes = {row[0] for row in conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type = 'index'")}
    model_indexes = {ix.name for table in db.metadata.tables.values() for ix in table.indexes}
    diff = [d for d in diff if not (d[0] == 'remove_table' and _is_ignored_table(d[1].name))]
    return diff + [('missing_index', name) for name in sorted(model_indexes - db_indexes)]


def _close():
    db.session.remove()
    db.engine.dispose()


def test_create_app_does_not_create_tables(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        assert inspect(db.engine).get_table_names() == []
        _close()


def test_upgrade_on_fresh_database_matches_models(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS)
        assert _schema_diff() == []
        _close()


def test_downgrade_to_base_and_back(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS)
        downgrade(directory=MIGRATIONS, revision='base')
        assert set(inspect(db.engine).get_table_names()) <= {'alembic_version'}
        upgrade(directory=MIGRATIONS)
        assert _schema_diff() == []
        _close()


def test_running_migrations_keeps_app_logging_enabled(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS)
        _close()
    assert not app.logger.disabled


def _raw(sql, **params):
    from sqlalchemy import text
    with db.engine.begin() as conn:
        return conn.execute(text(sql), params).fetchall() if sql.lstrip().upper().startswith('SELECT') \
            else conn.execute(text(sql), params)


def _insert_user(email):
    _raw("INSERT INTO user (name, email, password_hash) VALUES ('U', :email, 'x')", email=email)


def test_upgrade_normalizes_existing_emails_and_enforces_case_insensitive_uniqueness(tmp_path):
    import pytest
    from sqlalchemy.exc import IntegrityError
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision=BASELINE)
        _insert_user('  Mixed.Case@Example.COM ')
        _insert_user('plain@example.com')

        upgrade(directory=MIGRATIONS)

        emails = sorted(row[0] for row in _raw('SELECT email FROM user'))
        assert emails == ['mixed.case@example.com', 'plain@example.com']
        with pytest.raises(IntegrityError):
            _insert_user('PLAIN@example.com')
        _close()


def test_upgrade_refuses_emails_that_collide_after_normalizing(tmp_path, capsys):
    import pytest
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision=BASELINE)
        _insert_user('dup@example.com')
        _insert_user('DUP@example.com')

        # Flask-Migrate logs the migration's error and exits 1, as `flask db upgrade` does.
        with pytest.raises(SystemExit) as excinfo:
            upgrade(directory=MIGRATIONS)
        assert excinfo.value.code == 1
        err = capsys.readouterr().err
        assert 'differ only by case' in err
        assert 'dup@example.com' not in err.lower()

        assert _raw('SELECT version_num FROM alembic_version') == [(BASELINE,)]
        assert sorted(r[0] for r in _raw('SELECT email FROM user')) == ['DUP@example.com', 'dup@example.com']
        _close()


# ---- Phase 4: tag user-scoping is data-preservation work ----

PRE_TAG_SCOPING_REVISION = 'f2e8b4d6a1c9'


def _insert_user_row(user_id, email):
    _raw("INSERT INTO user (id, name, email, password_hash) VALUES (:id, 'U', :email, 'x')",
         id=user_id, email=email)


def _insert_note_row(note_id, user_id, title='N'):
    _raw('INSERT INTO note (id, user_id, title, content) VALUES (:id, :uid, :title, :title)',
         id=note_id, uid=user_id, title=title)


def _insert_tag_row(tag_id, name):
    _raw("INSERT INTO tag (id, name) VALUES (:id, :name)", id=tag_id, name=name)


def _link_note_tag(note_id, tag_id):
    _raw('INSERT INTO note_tags (note_id, tag_id) VALUES (:nid, :tid)', nid=note_id, tid=tag_id)


def test_upgrade_assigns_single_user_tag_to_its_owner(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision=PRE_TAG_SCOPING_REVISION)
        _insert_user_row(1, 'a@example.com')
        _insert_note_row(1, 1)
        _insert_tag_row(1, 'solo')
        _link_note_tag(1, 1)

        upgrade(directory=MIGRATIONS)

        rows = _raw('SELECT id, user_id, name FROM tag')
        assert rows == [(1, 1, 'solo')]
        _close()


def test_upgrade_deletes_tags_with_no_notes(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision=PRE_TAG_SCOPING_REVISION)
        _insert_tag_row(1, 'orphan')

        upgrade(directory=MIGRATIONS)

        assert _raw('SELECT * FROM tag') == []
        _close()


def test_upgrade_splits_a_tag_shared_across_users(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision=PRE_TAG_SCOPING_REVISION)
        _insert_user_row(1, 'a@example.com')
        _insert_user_row(2, 'b@example.com')
        _insert_note_row(1, 1, 'note-a')
        _insert_note_row(2, 2, 'note-b')
        _insert_tag_row(1, 'shared')
        _link_note_tag(1, 1)
        _link_note_tag(2, 1)

        upgrade(directory=MIGRATIONS)

        tags = _raw('SELECT id, user_id, name FROM tag ORDER BY user_id')
        assert [(uid, name) for (_id, uid, name) in tags] == [(1, 'shared'), (2, 'shared')]
        tag_by_user = {uid: tid for (tid, uid, _name) in tags}

        links = _raw('SELECT note_id, tag_id FROM note_tags')
        assert set(links) == {(1, tag_by_user[1]), (2, tag_by_user[2])}
        _close()


def test_upgrade_drops_note_summary_without_losing_embeddings(tmp_path):
    # Regression test: batch-altering `note` to drop `summary` must not use
    # SQLite batch mode's default copy/drop/rename recreate, since dropping
    # the original `note` table fires the ON DELETE CASCADE on
    # note_embeddings.note_id and index_job.note_id as if every note were
    # deleted - silently wiping every embedding. See the migration's
    # `recreate='never'` comment.
    app = _file_app(tmp_path)
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision=PRE_TAG_SCOPING_REVISION)
        _insert_user_row(1, 'a@example.com')
        _insert_note_row(1, 1)
        _raw("INSERT INTO note_embeddings (note_id, embedding, content_hash) VALUES (1, X'00', 'h')")
        _raw("INSERT INTO index_job (note_id, content_hash) VALUES (1, 'h')")

        upgrade(directory=MIGRATIONS)

        assert _raw('SELECT note_id FROM note_embeddings') == [(1,)]
        assert _raw('SELECT note_id FROM index_job') == [(1,)]
        with db.engine.connect() as conn:
            columns = {row[1] for row in conn.exec_driver_sql('PRAGMA table_info(note)').fetchall()}
        assert 'summary' not in columns
        _close()
