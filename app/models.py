from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


note_tags = db.Table('note_tags',
    db.Column('note_id', db.Integer, db.ForeignKey('note.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.relationship('Note', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    
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
    summary = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    source_type = db.Column(db.String(20), default='manual')
    source_filename = db.Column(db.String(255), nullable=True)
    is_pinned = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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

    def get_all_relationships(self):
        return Relationship.query.filter(
            (Relationship.source_note_id == self.id) | (Relationship.target_note_id == self.id)
        ).all()
    
    def get_related_notes(self, limit=5, min_similarity=0.7):
        rels = Relationship.query.filter(
            ((Relationship.source_note_id == self.id) | (Relationship.target_note_id == self.id)) &
            (Relationship.similarity_score >= min_similarity)
        ).order_by(Relationship.similarity_score.desc()).limit(limit).all()
        
        related = []
        for rel in rels:
            other = rel.target_note if rel.source_note_id == self.id else rel.source_note
            related.append((other, rel.similarity_score, rel.relationship_type))
        return related
    
    def __repr__(self):
        return f'<Note {self.title}>'


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'


class NoteEmbedding(db.Model):
    """Stores each note's semantic embedding vector.

    Previously created via raw SQL in app/__init__.py instead of a
    SQLAlchemy model, which meant no ORM validation, no migration
    tracking, and every read/write going through hand-written text()
    queries in embedding_service.py. This model replaces that raw table
    definition; the table name/columns are kept identical so existing
    databases need no migration.
    """
    __tablename__ = 'note_embeddings'

    note_id = db.Column(db.Integer, db.ForeignKey('note.id', ondelete='CASCADE'), primary_key=True)
    embedding = db.Column(db.LargeBinary, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<NoteEmbedding note_id={self.note_id}>'


class Relationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False, index=True)
    target_note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False, index=True)
    similarity_score = db.Column(db.Float, nullable=False)
    relationship_type = db.Column(db.String(20), default='semantic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('source_note_id', 'target_note_id', name='unique_relationship'),
        db.CheckConstraint('source_note_id != target_note_id', name='no_self_relationship'),
    )
    
    def __repr__(self):
        return f'<Relationship {self.source_note_id} -> {self.target_note_id} ({self.similarity_score:.2f})>'