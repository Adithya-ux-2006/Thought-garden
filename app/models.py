from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import validates
from sqlalchemy.types import TypeDecorator
from app import db


note_tags = db.Table('note_tags',
    db.Column('note_id', db.Integer, db.ForeignKey('note.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


def normalize_email(value):
    return value.strip().lower() if isinstance(value, str) else value


def utcnow():
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Stores naive UTC (same on-disk format SQLite has always used here -
    no migration needed to switch), but every value that passes through
    Python is timezone-aware UTC. SQLite has no real timezone type and its
    driver silently drops tzinfo on read, so marking the underlying column
    `DateTime(timezone=True)` alone would round-trip aware datetimes back
    as naive ones without warning - this type reattaches `tzinfo=utc` on
    the way out instead, so every `Note.created_at`-style value the app
    ever touches is aware, and naive/aware subtraction bugs are caught
    immediately rather than only when they happen to involve real
    wall-clock time zones."""
    impl = db.DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(UTCDateTime, default=utcnow)
    notes = db.relationship('Note', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    # Backstop for rows written outside the ORM (raw SQL, older data).
    __table_args__ = (db.Index('uq_user_email_lower', db.func.lower(email), unique=True),)

    @validates('email')
    def _normalize_email(self, key, value):
        return normalize_email(value)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    source_type = db.Column(db.String(20), default='manual')
    source_filename = db.Column(db.String(255), nullable=True)
    is_pinned = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(UTCDateTime, default=utcnow, index=True)
    updated_at = db.Column(UTCDateTime, default=utcnow, onupdate=utcnow)
    
    tags = db.relationship('Tag', secondary=note_tags, lazy='subquery',
                          backref=db.backref('notes', lazy=True))
    relationships = db.relationship('Relationship',
        foreign_keys='Relationship.source_note_id',
        backref='source_note', lazy='dynamic', cascade='all, delete-orphan')
    inverse_relationships = db.relationship('Relationship',
        foreign_keys='Relationship.target_note_id',
        backref='target_note', lazy='dynamic', cascade='all, delete-orphan')
    # passive_deletes intentionally NOT set: SQLite only enforces
    # ON DELETE CASCADE at the DB level when PRAGMA foreign_keys=ON is
    # set per-connection, which SQLAlchemy does not do by default. Without
    # passive_deletes, SQLAlchemy loads and deletes the related row itself
    # (an extra SELECT before DELETE) instead of relying on that pragma -
    # slightly more work per delete, but correct regardless of DB config.
    embedding_row = db.relationship('NoteEmbedding', backref='note', uselist=False,
        cascade='all, delete-orphan')
    index_job = db.relationship('IndexJob', backref='note', uselist=False,
        cascade='all, delete-orphan')

    def get_related_notes(self, limit=5, min_similarity=0.0):
        """(other_note, Relationship) pairs, strongest first."""
        # Stored relationships already start at SIMILARITY_THRESHOLD, so the
        # default must not filter on top of it.
        rels = Relationship.query.filter(
            ((Relationship.source_note_id == self.id) | (Relationship.target_note_id == self.id)) &
            (Relationship.similarity_score >= min_similarity)
        ).order_by(Relationship.similarity_score.desc()).limit(limit).all()

        return [(rel.target_note if rel.source_note_id == self.id else rel.source_note, rel)
                for rel in rels]
    
    def __repr__(self):
        return f'<Note {self.title}>'


class Tag(db.Model):
    # Scoped per user like Note: a shared tag row would leak one user's
    # tag suggestions and counts into another's garden.
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(UTCDateTime, default=utcnow)

    # Tag.notes comes from Note.tags's backref below.

    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_tag_user_id_name'),
        # Exact-match uniqueness above doesn't stop the same user saving
        # both "AI" and "ai" as two rows - matches the case-insensitive
        # backstop already used for User.email (uq_user_email_lower).
        db.Index('uq_tag_user_id_name_lower', user_id, db.func.lower(name), unique=True),
    )

    def __repr__(self):
        return f'<Tag {self.name}>'


class NoteEmbedding(db.Model):
    """Stores each note's semantic embedding vector."""
    __tablename__ = 'note_embeddings'

    note_id = db.Column(db.Integer, db.ForeignKey('note.id', ondelete='CASCADE'), primary_key=True)
    embedding = db.Column(db.LargeBinary, nullable=False)
    # Hash of the exact text last embedded (see embedding_service.content_hash) -
    # lets the indexer skip re-embedding a note whose save didn't change
    # anything the embedding depends on. Nullable: rows written before this
    # column existed simply re-embed once on their next content change.
    content_hash = db.Column(db.String(64), nullable=True)
    updated_at = db.Column(UTCDateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self):
        return f'<NoteEmbedding note_id={self.note_id}>'


class IndexJob(db.Model):
    """One row per note that needs (re-)embedding - acts as a small durable
    queue for the background indexer worker (see app/services/indexer.py).

    A unique note_id means enqueuing is an upsert: a note saved twice before
    the worker gets to it collapses into one job instead of two.
    """
    __tablename__ = 'index_job'

    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id', ondelete='CASCADE'), nullable=False,
        unique=True, index=True)
    content_hash = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending | done | failed
    attempts = db.Column(db.Integer, nullable=False, default=0)
    model_version = db.Column(db.String(100), nullable=True)
    created_at = db.Column(UTCDateTime, default=utcnow)
    updated_at = db.Column(UTCDateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self):
        return f'<IndexJob note_id={self.note_id} status={self.status}>'


class Relationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False, index=True)
    target_note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False, index=True)
    similarity_score = db.Column(db.Float, nullable=False)
    relationship_type = db.Column(db.String(20), default='semantic')
    # Which scorer produced similarity_score - 'embedding' (cosine similarity,
    # comparable across all embedding-scored pairs) or 'keyword' (Jaccard-ish
    # overlap, a different scale entirely), so scores are only comparable
    # within one method.
    method = db.Column(db.String(20), nullable=False, default='embedding')
    created_at = db.Column(UTCDateTime, default=utcnow)
    updated_at = db.Column(UTCDateTime, default=utcnow, onupdate=utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('source_note_id', 'target_note_id', name='unique_relationship'),
        db.CheckConstraint('source_note_id != target_note_id', name='no_self_relationship'),
    )
    
    def __repr__(self):
        return f'<Relationship {self.source_note_id} -> {self.target_note_id} ({self.similarity_score:.2f})>'