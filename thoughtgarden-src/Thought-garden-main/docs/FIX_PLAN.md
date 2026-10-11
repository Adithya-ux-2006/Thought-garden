# Thought Garden Fix Plan

## FIX-001: CSRFProtect Initialization [P0 — COMPLETED]

**Problem:** `csrf_token()` undefined in Jinja2 templates. Every note create/view/edit page returns HTTP 500.

**Root Cause:** Flask-WTF installed but `CSRFProtect(app)` never called in app factory.

**Files:** `app/__init__.py`

**Fix:** Import `CSRFProtect` from `flask_wtf.csrf`, create instance `csrf = CSRFProtect()`, call `csrf.init_app(app)`.

**Verification:** All note pages load (200 status). Note creation works end-to-end.

---

## FIX-002: Lower Similarity Threshold [P1 — COMPLETED]

**Problem:** Only 2 relationships among 17 notes. ML Fundamentals had 0 connections.

**Root Cause:** Threshold 0.7 is too high for `all-MiniLM-L6-v2` embeddings. Most semantically related notes score 0.45-0.65.

**Measured similarities:**
- ML Fundamentals ↔ Deep Learning: 0.557
- ML Fundamentals ↔ Data Science: 0.571
- Neural Nets ↔ Deep Learning: 0.719 (only one above 0.7)
- IDS ↔ Network Security: 0.507

**Files:** `app/services/similarity_service.py`, `app/app/notes/routes.py`

**Fix:** Change default threshold from 0.7 to 0.45. Update hardcoded 0.7 in note view route.

**Verification:** 25+ relationships discovered. Knowledge Garden shows meaningful connections.

---

## FIX-003: Dark Mode + Template Variables [P2 — COMPLETED]

**Problem:** `dark_mode` variable undefined in base.html. Garden inline CSS hardcoded light colors.

**Root Cause:** Base template referenced `dark_mode` variable never passed by routes. Garden panel CSS used hardcoded white/gray.

**Files:** `app/templates/base.html`, `app/templates/garden/index.html`

**Fix:** Set `data-bs-theme="light"` as default. Use CSS variables in garden inline styles.

**Verification:** Dark mode toggle works. Garden panel respects theme.

---

## FIX-004: XSS Vulnerability [P2 — COMPLETED]

**Problem:** Note content rendered with `| safe` filter, allowing HTML injection.

**Root Cause:** Template used `{{ note.content | safe }}` which bypasses Jinja2 escaping.

**Files:** `app/templates/notes/view.html`

**Fix:** Change to `{{ note.content }}` (escaped by default).

**Verification:** User content displayed as plain text.

---

## FIX-005: Dead Code + Imports [P3 — COMPLETED]

**Problem:** Unused imports, duplicate functions, confusing service re-exports.

**Files:** `app/services/__init__.py`, `app/services/document_service.py`, `app/app/notes/routes.py`

**Fix:** Remove `uuid` import, `re` import. Clean up service `__init__.py` to avoid shadowing `extract_keywords`.

**Verification:** No import errors. Services work correctly.

---

## Remaining Known Issues

| ID | Priority | Issue | Status |
|----|----------|-------|--------|
| REM-001 | P2 | Category filter checkboxes in garden have no JS logic | NOT FIXED |
| REM-002 | P3 | `extensions.py` defines unused `db` and `login_manager` | NOT FIXED |
| REM-003 | P3 | `note_embeddings` created via raw SQL, not SQLAlchemy model | NOT FIXED |
| REM-004 | P3 | Custom Pagination class duplicates Flask-SQLAlchemy | NOT FIXED |
| REM-005 | P3 | `cosine_similarity` defined in both similarity_service and search_service | NOT FIXED |
| REM-006 | P3 | No loading states during AI processing | NOT FIXED |
| REM-007 | P3 | Debug mode enabled (acceptable for dev) | NOT FIXED |
