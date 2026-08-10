# Thought Garden — Project History

## Version 1.0 — Initial Build (Completed)

### Features Built
1. User registration and authentication (Flask-Login, Werkzeug password hashing)
2. Notes CRUD with categories, tags, pin, archive
3. AI similarity engine (sentence-transformers + cosine similarity)
4. Keyword extraction (TF-IDF via scikit-learn)
5. Hybrid search (keyword + semantic with weighted scoring)
6. Knowledge Graph visualization (vis-network)
7. Focus mode (graph exploration centered on a single note)
8. Document import (PDF/TXT/Markdown)
9. Dashboard with metrics
10. Dark mode toggle
11. Tag autocomplete
12. Pagination across all list views

### Architecture
- Flask application factory pattern
- Blueprint separation: main, notes, garden, search, auth
- Service layer: embedding, similarity, keyword, search, document
- SQLAlchemy ORM with SQLite database
- sentence-transformers (all-MiniLM-L6-v2) for embeddings
- vis-network for graph visualization

### Seed Data
17 notes across 5 categories:
- AI (6 notes): ML, Neural Nets, Deep Learning, NLP, Computer Vision, Data Science
- Cybersecurity (3 notes): IDS, Network Security, Adaptive Threats
- Software Engineering (3 notes): Agile, Requirements, Testing
- Operating Systems (3 notes): CPU Scheduling, Process Management, Deadlock
- Research (2 notes): Adaptive Cybersecurity paper, Transformer Architecture paper

### Pre-Fix State
- 17 notes, 0 connections visible (threshold 0.7 too high)
- Note create/view/edit returned HTTP 500 (CSRFProtect not initialized)
- Dark mode variable undefined in base template
- XSS vulnerability in note view

---

## Version 1.1 — Critical Bug Fixes (Completed)

### Fix 1: CSRFProtect Initialization
- **Problem:** All note pages returned HTTP 500
- **Fix:** Added `csrf.init_app(app)` in app factory
- **Result:** All pages load successfully

### Fix 2: Similarity Threshold
- **Problem:** Only 2 relationships among 17 notes
- **Fix:** Lowered from 0.7 to 0.45
- **Result:** 25+ relationships discovered

### Fix 3: Dark Mode + XSS
- **Problem:** Undefined variable, hardcoded light-mode CSS, XSS vulnerability
- **Fix:** Set default theme, use CSS variables, remove `| safe` filter
- **Result:** Theme works correctly, content is safely escaped

---

## Current State
- All 12 major pages load without errors
- Note CRUD fully functional
- AI pipeline discovers meaningful connections
- Knowledge graph shows 25+ edges with correct semantics
- Search works (keyword + semantic)
- Document import works (PDF/TXT/MD)
- Seed data provides realistic demo experience

## Known Limitations
- Category filter checkboxes have no JavaScript logic
- Duplicate code across services
- `note_embeddings` table not modeled in SQLAlchemy
- Debug mode enabled (development only)
