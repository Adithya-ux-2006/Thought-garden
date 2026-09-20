from flask import Flask
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


def create_app(config_overrides=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if Config.SECRET_KEY == 'dev-secret-key':
        app.logger.warning(
            'SECRET_KEY is not set - falling back to an insecure default. '
            'Set SECRET_KEY in your environment or .env file before deploying.'
        )
    app.config['MAX_CONTENT_LENGTH'] = Config.UPLOAD_MAX_SIZE_MB * 1024 * 1024

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

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

    with app.app_context():
        # note_embeddings (NoteEmbedding model) is created here too - it
        # used to need a separate raw CREATE TABLE because it wasn't a
        # SQLAlchemy model; now that it is, create_all() covers it.
        db.create_all()

    return app
