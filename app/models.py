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