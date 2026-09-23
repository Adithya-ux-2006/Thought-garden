import os

from dotenv import load_dotenv

# Load .env before any os.environ.get() calls read them.
load_dotenv()


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
    # Off unless explicitly enabled - a blank or typo'd value must not turn
    # the debugger on.
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', '0').strip().lower() in {'1', 'true', 'yes', 'on'}

    # --- Cookies --- Secure only outside debug, so local http:// dev still works.
    SESSION_COOKIE_SECURE = not FLASK_DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = not FLASK_DEBUG
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # --- SQLAlchemy ---
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///thought_garden.db')
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
