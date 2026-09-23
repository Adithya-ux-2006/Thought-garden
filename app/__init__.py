import logging
import uuid

from flask import Flask, jsonify, render_template, request, g
from flask_sqlalchemy import SQLAlchemy
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


def _validate_secret_key(app):
    """Ensure SECRET_KEY is set to a real value in production.

    In debug mode, the insecure development fallback is allowed with a
    warning.  In production (debug off), the app refuses to start — a
    missing or default SECRET_KEY means sessions, CSRF tokens, and
    signed cookies are trivially forgeable.

    The actual secret value is never logged or included in the error
    message.
    """
    key = Config.SECRET_KEY
    is_insecure = not key or key == DEV_SECRET_KEY

    if not is_insecure:
        return  # real key provided — nothing to do

    if Config.FLASK_DEBUG:
        app.logger.warning(
            'SECRET_KEY is not set - falling back to an insecure default. '
            'Set SECRET_KEY in your environment or .env file before deploying.'
        )
        return

    # Production with no real key — refuse to start.
    raise RuntimeError(
        'SECRET_KEY must be set to a secure, random value before starting '
        'in production (FLASK_DEBUG=0). The default development key is not '
        'safe for use in production — sessions, CSRF tokens, and signed '
        'cookies would be trivially forgeable. Set SECRET_KEY in your '
        'environment or .env file to a long, random string.'
    )


def create_app(config_overrides=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    _configure_logging(app)

    _validate_secret_key(app)
    app.config['MAX_CONTENT_LENGTH'] = Config.UPLOAD_MAX_SIZE_MB * 1024 * 1024

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

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

    with app.app_context():
        # note_embeddings (NoteEmbedding model) is created here too - it
        # used to need a separate raw CREATE TABLE because it wasn't a
        # SQLAlchemy model; now that it is, create_all() covers it.
        db.create_all()

    return app
