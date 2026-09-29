import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.models import Relationship


def _file_app(tmp_path, name='app.db'):
    return create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{(tmp_path / name).as_posix()}',
        'SECRET_KEY': 'test-secret-key',
    })


def test_sqlite_connections_get_pragmas(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        conn = db.session.connection()
        assert conn.exec_driver_sql('PRAGMA foreign_keys').scalar() == 1
        assert conn.exec_driver_sql('PRAGMA busy_timeout').scalar() >= 5000
        assert conn.exec_driver_sql('PRAGMA journal_mode').scalar() == 'wal'
        db.session.remove()
        db.engine.dispose()


def test_foreign_keys_are_enforced(tmp_path):
    app = _file_app(tmp_path)
    with app.app_context():
        db.create_all()
        db.session.add(Relationship(source_note_id=998, target_note_id=999, similarity_score=0.5))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        db.session.remove()
        db.engine.dispose()
