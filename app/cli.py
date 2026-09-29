import os

import click
from alembic.config import Config as AlembicConfig
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

from app import db

MIGRATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'migrations'))


def schema_is_current():
    """True when the database is at the latest Alembic revision."""
    config = AlembicConfig()
    config.set_main_option('script_location', MIGRATIONS_DIR)
    heads = set(ScriptDirectory.from_config(config).get_heads())
    with db.engine.connect() as conn:
        current = set(MigrationContext.configure(conn).get_current_heads())
    return current == heads


DEMO_EMAIL = 'demo@thoughtgarden.app'
DEMO_PASSWORD = 'demo1234'


@click.command('seed-demo')
def seed_demo():
    """Create the local demo account with the starter garden."""
    from flask import current_app
    from app.models import User
    from app.services import indexer
    from app.services.onboarding_service import add_starter_notes

    if User.query.filter_by(email=DEMO_EMAIL).first():
        click.echo(f'Demo user {DEMO_EMAIL} already exists; nothing to do.')
        return
    user = User(name='Demo User', email=DEMO_EMAIL)
    user.set_password(DEMO_PASSWORD)
    db.session.add(user)
    db.session.commit()
    notes = add_starter_notes(user, source_type='manual', backdate=True)
    # A one-off interactive command, unlike a web request: embed the
    # starter notes synchronously right away rather than leaving them
    # queued for the background worker, so the demo garden's connections
    # are embedding-tier from the first login instead of a mix that only
    # upgrades once the worker happens to run.
    indexer.process_pending(current_app._get_current_object())
    click.echo(f'Created {len(notes)} demo notes.')
    click.echo(f'Log in with {DEMO_EMAIL} / {DEMO_PASSWORD} (local demo only - never on a shared server).')


@click.command('reindex')
def reindex():
    """Re-embed every note and recompute relationships for every user."""
    from flask import current_app
    from app.models import Note, User
    from app.services import indexer
    from app.services.similarity_service import rebuild_user_graph

    indexer.process_pending(current_app._get_current_object())

    note_count = 0
    relationship_count = 0
    for user in User.query.all():
        relationship_count += rebuild_user_graph(user.id)
        note_count += Note.query.filter_by(user_id=user.id, is_archived=False).count()
    click.echo(f'{relationship_count} relationships across {note_count} notes.')


def register_commands(app):
    app.cli.add_command(seed_demo)
    app.cli.add_command(reindex)
