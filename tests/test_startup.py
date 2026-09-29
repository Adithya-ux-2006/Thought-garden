import os
import runpy

import pytest
from flask import Flask
from flask_migrate import upgrade

from app import create_app, db
from app.models import User
from config import Config

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RUN_PY = os.path.join(REPO_ROOT, 'run.py')
MIGRATIONS = os.path.join(REPO_ROOT, 'migrations')


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Point run.py's create_app() at a throwaway DB, never the real one."""
    uri = f'sqlite:///{(tmp_path / "startup.db").as_posix()}'
    monkeypatch.setattr(Config, 'SQLALCHEMY_DATABASE_URI', uri)
    monkeypatch.setattr(Config, 'SECRET_KEY', 'test-secret-key')
    calls = []
    monkeypatch.setattr(Flask, 'run', lambda self, *a, **k: calls.append((a, k)))

    def no_backfill(*a, **k):
        raise AssertionError('startup must not run a relationship backfill')
    monkeypatch.setattr('app.services.similarity_service.rebuild_user_graph', no_backfill)

    # create_app() only skips starting the real worker thread when
    # TESTING is set, which isolated_config's whole point is to test
    # without (it's exercising the actual run.py startup path). Stub the
    # worker start itself instead, so this test doesn't spawn a thread
    # that tries to download a model over the network.
    monkeypatch.setattr('app.services.indexer.start_worker', lambda *a, **k: None)
    return uri, calls


def _migrate(uri):
    app = create_app({'SQLALCHEMY_DATABASE_URI': uri, 'SECRET_KEY': 'test-secret-key'})
    with app.app_context():
        upgrade(directory=MIGRATIONS)
        db.engine.dispose()
    return app


def test_run_py_starts_without_seeding_or_backfill(isolated_config):
    uri, calls = isolated_config
    app = _migrate(uri)

    runpy.run_path(RUN_PY, run_name='__main__')

    assert len(calls) == 1
    with app.app_context():
        assert User.query.count() == 0
        db.engine.dispose()


def test_run_py_refuses_unmigrated_database(isolated_config):
    _uri, calls = isolated_config

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(RUN_PY, run_name='__main__')

    # sys.exit(<str>) exits non-zero and the interpreter prints the string to stderr.
    assert 'flask db upgrade' in str(excinfo.value.code)
    assert calls == []
