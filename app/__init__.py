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

# The vendored vis-network 9.1.9 standalone bundle injects its own CSS as
# <style> elements (an empty one first, then its content). These hashes allow
# exactly those stylesheets and nothing else; recompute them if vis-network is
# upgraded (tests/test_browser_smoke.py fails on any CSP violation).
VIS_NETWORK_STYLE_HASHES = (
    "'sha256-47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU='",
    "'sha256-OutIf5hnp68ctx4ThtV5J02g5HTJ5bbu/hkNfqVXWWo='",
    "'sha256-4cgFR0//m8/eHo2G/esYsuZetUHlzCUWYM59sfgE9zY='",
    "'sha256-uepMTym1NwItBa/XV6ef6fQobLL0A0CNVDM5km5L+nQ='",
    "'sha256-gGUn/VMBXCeWm86qX/pOf+4ZDSbe0JcaXXb4rJjw1mA='",
    "'sha256-QuPewnJYr+SnQiTnCNHFBw99ExTsz9f8w5320PimEPw='",
    "'sha256-IY7YKNHjbzQ1NfAKrBZvBZohgXMtxrqB9PaqhAaT3vg='",
    "'sha256-QE7TOEDW7YIlMzvUUnm8boDWeNBN7PBbaaYJjnp34WI='",
)

# Every script, stylesheet and font is served from /static, so no inline
# script or style attribute is ever needed. img-src allows https: so Markdown
# images in notes still render; everything else is same-origin only.
CONTENT_SECURITY_POLICY = '; '.join([
    "default-src 'self'",
    "script-src 'self'",
    # Hash sources cover <style> elements only, so style="" attributes stay blocked.
    f"style-src 'self' {' '.join(VIS_NETWORK_STYLE_HASHES)}",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


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

    @app.after_request
    def _add_security_headers(response):
        response.headers['Content-Security-Policy'] = CONTENT_SECURITY_POLICY
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
        # A tag equal to the note's category would repeat the category badge
        # shown right next to it.
        if not category:
            return list(tags)
        category_lower = category.strip().lower()
        return [t for t in tags if t.name.strip().lower() != category_lower]

    from app.services.similarity_service import relationship_label
    app.template_filter('relationship_label')(relationship_label)

    from app.services.markdown_service import render_markdown
    app.template_filter('markdown')(render_markdown)

    from app.services.category_service import category_badge_class, garden_category_metadata
    app.template_filter('category_badge_class')(category_badge_class)
    app.jinja_env.globals['GARDEN_CATEGORIES'] = garden_category_metadata()

    return app
