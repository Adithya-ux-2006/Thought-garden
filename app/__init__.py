from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os

# Load variables from a .env file (if present) into the process environment
# before any os.environ.get() calls below read them. Without this, values
# in .env were silently ignored and every config fell back to its default.
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access your garden.'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()


def create_app(config_overrides=None):
    app = Flask(__name__, instance_relative_config=True)

    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        secret_key = 'dev-secret-key'
        app.logger.warning(
            'SECRET_KEY is not set - falling back to an insecure default. '
            'Set SECRET_KEY in your environment or .env file before deploying.'
        )
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///thought_garden.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('UPLOAD_MAX_SIZE_MB', 10)) * 1024 * 1024
    
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