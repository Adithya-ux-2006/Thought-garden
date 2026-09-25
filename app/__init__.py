import logging
import uuid

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access your garden.'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()


class RequestIDFilter(logging.Filter):
    """Inject the current request's ID into every log record so it appears
    in the formatted output without each caller passing it explicitly."""

    def filter(self, record):
        try:
            record.request_id = g.get('request_id', '-')
        except RuntimeError:
            # Outside a Flask application context (e.g. during startup or
            # in background threads before a request), g is unbound.
            record.request_id = '-'
        return True


def _configure_logging(app):
    """Set up a consistent log format with request ID and timestamp.

    Uses Flask's built-in logger — no external logging framework needed.
    The format includes request_id (or '-' outside a request context),
    timestamp, level, module, and message.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(request_id)s %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    ))
    handler.addFilter(RequestIDFilter())

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.addFilter(RequestIDFilter())


DEV_SECRET_KEY = 'dev-secret-key'
# Publicly known values (code default, old .env.example) - never valid in production.
INSECURE_SECRET_KEYS = {'', DEV_SECRET_KEY, 'dev-secret-key-change-in-production'}


def _validate_secret_key(app):
    """Ensure SECRET_KEY is set to a real value in production.

    In debug mode, the insecure development fallback is allowed with a
    warning.  In production (debug off), the app refuses to start — a
    missing or default SECRET_KEY means sessions, CSRF tokens, and
    signed cookies are trivially forgeable.

    The actual secret value is never logged or included in the error
    message.
    """
    key = app.config.get('SECRET_KEY') or ''
    if key not in INSECURE_SECRET_KEYS:
        return  # real key provided — nothing to do

    if app.config.get('FLASK_DEBUG'):
        app.logger.warning(
            'SECRET_KEY is not set - falling back to an insecure default. '
            'Set SECRET_KEY in your environment or .env file before deploying.'
        )
        if not key:
            app.config['SECRET_KEY'] = DEV_SECRET_KEY
        return

    # Production with no real key — refuse to start.
    raise RuntimeError(
        'SECRET_KEY must be set to a secure, random value before starting '
        'in production (FLASK_DEBUG=0). The default development key is not '
        'safe for use in production — sessions, CSRF tokens, and signed '
        'cookies would be trivially forgeable. Set SECRET_KEY in your '
        'environment or .env file to a long, random string.'
    )


def _set_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.execute('PRAGMA busy_timeout=5000')
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.close()


def create_app(config_overrides=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    _configure_logging(app)

    if config_overrides:
        app.config.update(config_overrides)

    app.config['MAX_CONTENT_LENGTH'] = app.config['UPLOAD_MAX_SIZE_MB'] * 1024 * 1024

    _validate_secret_key(app)

    db.init_app(app)
    with app.app_context():
        if db.engine.dialect.name == 'sqlite':
            event.listen(db.engine, 'connect', _set_sqlite_pragmas)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.auth.rate_limit import FailedLoginLimiter
    app.extensions['login_limiter'] = FailedLoginLimiter()

    # --- Request ID middleware ---
    @app.before_request
    def _assign_request_id():
        g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex

    @app.after_request
    def _add_request_id_header(response):
        response.headers['X-Request-ID'] = g.get('request_id', '-')
        return response

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        app.logger.warning('404 Not Found: %s %s', request.method, request.path)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify(error='Not found', request_id=g.get('request_id', '-')), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_too_large(e):
        app.logger.warning('413 Request Too Large: %s %s', request.method, request.path)
        message = f"File too large. Maximum size: {app.config['UPLOAD_MAX_SIZE_MB']} MB."
        if request.accept_mimetypes.best == 'application/json':
            return jsonify(error=message, request_id=g.get('request_id', '-')), 413
        flash(message, 'danger')
        # The import endpoint is POST-only; every other form page is GET-able at its own path.
        if request.endpoint == 'notes.import_document':
            return redirect(url_for('notes.create'))
        return redirect(request.path)

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.exception('500 Internal Server Error: %s %s', request.method, request.path)
        db.session.rollback()
        if request.accept_mimetypes.best == 'application/json':
            return jsonify(error='Internal server error', request_id=g.get('request_id', '-')), 500
        return render_template('errors/500.html'), 500

    from app.models import User, Note, Tag, Relationship, NoteEmbedding

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.notes import bp as notes_bp
    app.register_blueprint(notes_bp)

    from app.garden import bp as garden_bp
    app.register_blueprint(garden_bp)

    from app.search import bp as search_bp
    app.register_blueprint(search_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.cli import register_commands
    register_commands(app)

    # One persistent worker thread per process, loaded once here - never
    # per request. Skipped under pytest (TESTING=True in every fixture);
    # tests instead call indexer.process_pending(app) directly.
    if not app.config.get('TESTING'):
        from app.services import indexer
        indexer.start_worker(app)

    @app.template_filter('display_tags')
    def display_tags_filter(tags, category):
        # Seed data (and real user habit) often tags a note with its own
        # category name, which then repeats the already-shown category
        # badge as the first tag right next to it - same word twice with
        # no added information. Used everywhere a note's tags are rendered
        # alongside its category badge.
        if not category:
            return list(tags)
        category_lower = category.strip().lower()
        return [t for t in tags if t.name.strip().lower() != category_lower]

    from app.services.similarity_service import relationship_label
    app.template_filter('relationship_label')(relationship_label)

    from app.services.category_service import garden_category_metadata
    app.jinja_env.globals['GARDEN_CATEGORIES'] = garden_category_metadata()

    return app
