import os

from dotenv import load_dotenv

# Load .env before any os.environ.get() calls read them.
load_dotenv()


def _default_sqlite_uri() -> str:
    """SQLite location that is actually writable where the app runs.

    Streamlit Community Cloud mounts the repo read-only, so Flask's default
    (relative URI -> <app>/instance/thought_garden.db) dies in db.create_all()
    with an OperationalError. Probe the instance folder and fall back to /tmp
    there; locally nothing changes.
    """
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    try:
        os.makedirs(instance_dir, exist_ok=True)
        probe = os.path.join(instance_dir, '.write_test')
        with open(probe, 'w'):
            pass
        os.remove(probe)
        db_path = os.path.join(instance_dir, 'thought_garden.db').replace('\\', '/')
        return f'sqlite:///{db_path}'
    except OSError:
        return 'sqlite:////tmp/thought_garden.db'


class Config:
    """Central configuration. Every env var the application reads is listed
    here with its default. Modules import from Config instead of calling
    os.environ.get() directly — one place to see every setting, its type,
    and its default.

    Environment-variable names and defaults are unchanged from the
    pre-refactor code so existing .env files, deployment scripts, and
    documentation keep working.
    """

    # --- Flask core ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', '1').lower() not in {'0', 'false', 'no'}

    # --- SQLAlchemy ---
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or _default_sqlite_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---
    UPLOAD_MAX_SIZE_MB = int(os.environ.get('UPLOAD_MAX_SIZE_MB', 10))

    # --- Embedding / similarity ---
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', 0.45))
    MAX_RELATED_NOTES = int(os.environ.get('MAX_RELATED_NOTES', 5))
    KEYWORD_SIMILARITY_THRESHOLD = float(os.environ.get('KEYWORD_SIMILARITY_THRESHOLD', 0.18))

    # --- Startup / server ---
    AUTO_SEED = os.environ.get('AUTO_SEED', '1').lower() not in {'0', 'false', 'no'}
    PORT = int(os.environ.get('PORT', 5000))
