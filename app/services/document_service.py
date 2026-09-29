import os
from flask import current_app
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader


ALLOWED_EXTENSIONS = {'txt', 'md', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file(file):
    if not file or not file.filename:
        return False, 'No file selected.'
    
    if not allowed_file(file.filename):
        return False, 'Unsupported file type. Allowed: txt, md, pdf'
    
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    limit_mb = current_app.config['UPLOAD_MAX_SIZE_MB']
    if size > limit_mb * 1024 * 1024:
        return False, f'File too large. Maximum size: {limit_mb} MB.'
    
    return True, None


def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return '\n\n'.join(text)
    except Exception as e:
        raise ValueError(f'Failed to extract text from PDF: {str(e)}')


def extract_text_from_txt(file):
    try:
        return file.read().decode('utf-8')
    except UnicodeDecodeError:
        file.seek(0)
        return file.read().decode('latin-1')


def extract_text_from_md(file):
    return extract_text_from_txt(file)


def extract_text(file, filename):
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext == 'pdf':
        return extract_text_from_pdf(file)
    elif ext == 'txt':
        return extract_text_from_txt(file)
    elif ext == 'md':
        return extract_text_from_md(file)
    else:
        raise ValueError(f'Unsupported file type: {ext}')


def chunk_text(text, max_chunk_size=2000, overlap=200):
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chunk_size, len(text))
        
        if end < len(text):
            last_period = text.rfind('.', start, end)
            last_newline = text.rfind('\n', start, end)
            break_point = max(last_period, last_newline)
            if break_point > start:
                end = break_point + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break
        # A chunk shorter than the overlap (early break point) must not rewind.
        start = end - overlap if end - overlap > start else end

    return chunks


def generate_title_from_content(content, filename):
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and len(line) > 10 and len(line) < 150:
            return line[:100]
    
    name = os.path.splitext(filename)[0]
    return name.replace('_', ' ').replace('-', ' ').title()


def create_notes_from_document(user_id, content, filename, category=None):
    from app.models import Note, db
    from app.services import indexer
    from app.services.similarity_service import rebuild_user_graph

    chunks = chunk_text(content)

    notes = []
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            title = f"{generate_title_from_content(content, filename)} (Part {i+1})"
        else:
            title = generate_title_from_content(content, filename)

        note = Note(
            user_id=user_id,
            title=title,
            content=chunk,
            category=category,
            source_type=filename.rsplit('.', 1)[1].lower(),
            source_filename=filename
        )
        db.session.add(note)
        notes.append(note)

    db.session.commit()

    try:
        rebuild_user_graph(user_id)
    except Exception:
        current_app.logger.exception('Error building connections for notes imported from %s', filename)

    for note in notes:
        indexer.enqueue(note)

    return notes
