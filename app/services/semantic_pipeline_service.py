"""Durable semantic enrichment pipeline for every created or updated note."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import re
from threading import Lock

from flask import current_app

from app import db
from app.models import Note, SemanticJob, Tag
from app.services.embedding_service import generate_embedding
from app.services.keyword_service import extract_keywords
from app.services.similarity_service import update_relationships_for_note


_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='thought-garden-semantic')
_dispatch_lock = Lock()
_active_job_ids = set()

CATEGORY_TERMS = {
    'AI': {'ai', 'artificial', 'machine', 'learning', 'neural', 'model', 'nlp', 'vision', 'data'},
    'Cybersecurity': {'security', 'cybersecurity', 'threat', 'attack', 'network', 'malware', 'intrusion'},
    'Software Engineering': {'software', 'code', 'testing', 'agile', 'requirement', 'architecture', 'development'},
    'Operating Systems': {'operating', 'process', 'cpu', 'scheduling', 'deadlock', 'memory', 'kernel'},
    'Research': {'research', 'paper', 'experiment', 'hypothesis', 'study', 'analysis'},
    'Ideas': {'idea', 'concept', 'brainstorm', 'proposal', 'possibility'},
    'Study': {'study', 'learn', 'exam', 'revision', 'lesson', 'course'},
}


def infer_category(text):
    words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
    scores = {category: len(words & terms) for category, terms in CATEGORY_TERMS.items()}
    category, score = max(scores.items(), key=lambda item: item[1])
    return category if score else 'Ideas'


def generate_note_title(content):
    first_line = next((line.strip() for line in content.splitlines() if line.strip()), '')
    if 3 <= len(first_line) <= 100:
        return first_line.rstrip('.!?')
    words = content.strip().split()
    return ' '.join(words[:8]).rstrip('.,!?') or 'Untitled thought'


def enrich_note_metadata(note):
    combined = f'{note.title} {note.content}'
    if not note.category:
        note.category = infer_category(combined)
    if not note.tags:
        for keyword in extract_keywords(combined, max_keywords=4):
            name = keyword.title()
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
            note.tags.append(tag)
    db.session.commit()


def queue_semantic_pipeline(notes):
    """Create durable jobs after persistence and immediately build fallback links."""
    jobs = []
    for note in notes:
        enrich_note_metadata(note)
        update_relationships_for_note(note)
        job = SemanticJob.query.filter_by(note_id=note.id).first()
        if job is None:
            job = SemanticJob(note_id=note.id)
            db.session.add(job)
        else:
            job.status = 'queued'
            job.step = 'queued'
            job.error = None
            job.completed_at = None
        jobs.append(job)
    db.session.commit()

    app = current_app._get_current_object()
    if app.config.get('SEMANTIC_PIPELINE_BACKGROUND', not app.testing):
        for job in jobs:
            dispatch_job(app, job.id)
    else:
        for job in jobs:
            process_job(app, job.id, generate_embeddings=False)
    return jobs


def dispatch_job(app, job_id):
    with _dispatch_lock:
        if job_id in _active_job_ids:
            return
        _active_job_ids.add(job_id)
    _executor.submit(process_job, app, job_id)


def process_job(app, job_id, generate_embeddings=True):
    try:
        with app.app_context():
            job = db.session.get(SemanticJob, job_id)
            if job is None:
                return
            job.status = 'processing'
            job.step = 'metadata'
            job.attempts += 1
            job.error = None
            db.session.commit()

            note = db.session.get(Note, job.note_id)
            if note is None:
                db.session.delete(job)
                db.session.commit()
                return
            enrich_note_metadata(note)

            if generate_embeddings:
                job.step = 'embedding'
                db.session.commit()
                generate_embedding(note)

            job.step = 'connections'
            db.session.commit()
            update_relationships_for_note(note)

            job.status = 'completed'
            job.step = 'complete'
            job.completed_at = datetime.utcnow()
            db.session.commit()
    except Exception as error:
        with app.app_context():
            db.session.rollback()
            job = db.session.get(SemanticJob, job_id)
            if job:
                job.status = 'failed'
                job.step = 'fallback_ready'
                job.error = str(error)[:1000]
                db.session.commit()
    finally:
        with _dispatch_lock:
            _active_job_ids.discard(job_id)


def resume_semantic_jobs(app):
    with app.app_context():
        jobs = SemanticJob.query.filter(SemanticJob.status.in_(['queued', 'processing'])).all()
        for job in jobs:
            job.status = 'queued'
            job.step = 'queued'
        db.session.commit()
        job_ids = [job.id for job in jobs]
    for job_id in job_ids:
        dispatch_job(app, job_id)
