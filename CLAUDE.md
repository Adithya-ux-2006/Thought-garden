# CLAUDE.md — Thought Garden

Working notes for anyone (human or Claude) picking this repo back up. Keep this updated as things change — it exists so nobody has to re-derive context that's already been figured out once.

## What this is

Flask app: personal notes + AI-discovered knowledge graph. Register → get a copy of a 17-note "starter garden" → write/import notes → app scores similarity between notes → explore as a graph (vis-network) or hybrid search (keyword + semantic).

Stack: Flask, Flask-SQLAlchemy (SQLite), Flask-Login, Flask-WTF, sentence-transformers (`all-MiniLM-L6-v2`), scikit-learn/NumPy, PyPDF2, Bootstrap 5 + vanilla JS.

## Repo layout

```
run.py                 entry point — auto-seeds empty DB, backfills relationships, runs on :5000 (debug=True)
seed.py                demo data generator (17 notes across 5 categories)
app/__init__.py        app factory — CSRF, SQLAlchemy, Flask-Login, raw-SQL note_embeddings table
app/models.py          User, Note, Tag, Relationship
app/forms.py           Flask-WTF forms
app/{auth,notes,garden,search,main}/routes.py   blueprints
app/services/          embedding, similarity, keyword, search, document logic
app/templates/, app/static/
tests/test_app.py      pytest suite — currently broken, see below
docs/                  see "Docs are stale" below before trusting any of it
```

## Environment setup — read this before `pip install`

Python 3.13 + the pinned versions in `requirements.txt` **do not install out of the box**. Original pins (`scikit-learn==1.5.0`, `numpy==1.26.4`) have no prebuilt wheel for 3.13 and fall back to a source build that needs GCC ≥ 8.4; this machine only has MinGW 6.3.0, so it fails.

Fixed in `requirements.txt` (2026-09-18):
```
scikit-learn==1.5.2
numpy==1.26.4; python_version < "3.13"
numpy==2.1.2; python_version >= "3.13"
```
If you hit `meson.build ... ERROR: Cython requires python3 dependency` or `NumPy requires GCC >= 8.4` again, this is why — either the pin regressed or you're on a different Python minor version than expected.

First `pip install -r requirements.txt` is slow — `sentence-transformers` pulls in `torch`, which is a large download.

`.env.example` exists and `python-dotenv` is a dependency, but **nothing in the code calls `load_dotenv()`**. All env vars (`SECRET_KEY`, `SIMILARITY_THRESHOLD`, etc.) are silently ignored unless you wire this up or export them another way. Don't assume editing `.env` does anything.

### Verified working (2026-09-18)
```
python run.py
```
Boots clean, seeds 17 notes / 28 relationships, serves `/` and `/auth/login` at 200. Demo login: `demo@thoughtgarden.app` / `demo1234`.

## Known bugs / rough edges (found by full-repo read, not yet fixed unless noted)

- **Test suite is broken.** `tests/test_app.py` uses bare `app.app_context()` inside test bodies, but `app` at module scope is the pytest *fixture function*, not an app instance → `AttributeError` in ~half the tests. Nobody has been running these; don't trust "tests pass" without checking this first. `pytest` also isn't in `requirements.txt`.
- **Semantic embeddings are mostly dormant.** `update_relationships_for_note()` calls `get_embedding(..., generate_if_missing=False)` — embeddings are only used if they already exist, nothing generates them on note create/edit. They only get built the first time someone hits semantic search (`semantic_search` → `get_all_embeddings(user_id)`, default `generate_if_missing=True`), which then blocks that request on model load + encoding every note. Until then, all "AI connections" you see are the lightweight keyword/tag/category overlap scorer (`similarity_service.py:17`), not real embeddings.
- **Garden category filter checkboxes do nothing.** `app/templates/garden/index.html` has filter checkboxes (AI, Cybersecurity, SE, OS, Research) with no JS wired up. Dead UI. Tracked as `REM-001` in `docs/FIX_PLAN.md`, still unfixed.
- **`SECRET_KEY` defaults to a hardcoded dev string** (`app/__init__.py:18`) and, since dotenv isn't loaded, effectively always does — sessions aren't safe if this ever gets deployed as-is.
- **`debug=True` hardcoded** in `run.py:22`. Werkzeug debugger = remote code execution if this is ever exposed off localhost.
- **`Pagination` class defined twice** in `search_service.py`; the copy used by `semantic_search` is missing `iter_pages()`, so templates that call it on a semantic-only result set will crash.
- **`cosine_similarity` and `extract_keywords` each defined twice** (once in `similarity_service.py`, once in `search_service.py` / `keyword_service.py` respectively) with slightly different signatures/defaults. Easy to edit the wrong copy.
- **Embeddings stored as `pickle` blobs** in the raw-SQL `note_embeddings` table (`embedding_service.py:35`). Unpickling untrusted DB content is a code-exec surface; should be raw `numpy.tobytes()`.
- **`note.get_related_notes()` default `min_similarity=0.7`** (`models.py:59`) but relationships are actually stored/created at threshold 0.45 — every caller has to remember to override this or they silently get zero results. All current callers do pass `0.0`, but it's a landmine for new code.
- **N+1 queries** in `garden/routes.py` (`note.get_all_relationships()` called per node in a loop).
- `app/extensions.py` is dead code (duplicate `db`/`login_manager`, never imported).
- No `LICENSE` file despite README claiming MIT. No `CONTRIBUTING.md` despite ROADMAP linking one.
- No migrations (Alembic or similar) — any schema change currently means deleting the DB file.

## Docs are stale — don't trust them blindly

`docs/CURRENT_PROJECT_INVENTORY.md` in particular is **wrong in places**: references a `config.py` that doesn't exist, a `users.username` column that's actually `name`, `relationships.note1_id`/`note2_id` that are actually `source_note_id`/`target_note_id`, and template paths that don't match the real ones (e.g. `templates/notes/index.html` vs actual `templates/notes/list.html`). Treat it as historical, not authoritative — check `app/models.py` and the actual file tree instead.

`docs/SELF_AUDIT.md`, `docs/FIX_PLAN.md`, `docs/PROJECT_HISTORY.md` describe a prior debugging pass (CSRF fix, similarity threshold 0.7→0.45, XSS `|safe` removal, dark mode fix) — those fixes are real and present in current code. `docs/ROADMAP.md` v1.1+ items are all still just wishlist, not started.

README oversells slightly vs. actual code: claims SQLite FTS5 full-text search, but `search_service.py` actually uses plain `ILIKE '%q%'`. Keep this in mind if asked to "fix" search — it's not regressed, it just was never implemented as described.

## Repo/branch state log

- **2026-09-18** — Cloned from `https://github.com/Adithya-ux-2006/Thought-garden` into `D:\PROJECTS\SE`.
- **2026-09-18** — Created branch `feature/frontend-polish` off `main` (at commit `ef797c7`) for upcoming frontend work. Not started yet as of this writing.
- **2026-09-18** — Fixed `requirements.txt` (scikit-learn/numpy pins) so `pip install` + `python run.py` work on Python 3.13. Change is uncommitted on `feature/frontend-polish` as of this writing — check `git status` / `git log` to see if it's landed since.

- **2026-09-18** — Visual-only frontend pass on branch `feature/frontend-polish` (backend/routes/DB untouched). Scope: `app/templates/`, `app/static/css/style.css`, `app/static/js/main.js` (styling-only JS change).
  - New design system in `style.css`: earthy palette (moss green primary, terracotta accent) replacing default Bootstrap indigo, defined in both light and dark mode via CSS custom properties, plus a full remap of Bootstrap's own `--bs-*` variables so every `.btn-*`/`.badge`/`.alert`/`.bg-*` utility class repaints automatically without per-template edits.
  - Typography: added Google Fonts `Fraunces` (headings/serif) + `Inter` (body/sans, properly loaded now — previously referenced in CSS but never linked, so it silently fell back to system fonts).
  - Badges/alerts changed from flat saturated Bootstrap defaults to soft/tinted pill style.
  - Dashboard, notes list, and note detail templates restructured (stat cards, filter bar, note cards, page headers) — functionality, routes, and Jinja data usage unchanged.
  - Fixed a real dark-mode bug: `main.js` graph rendering (`initGarden`/`initFocusGraph`) had hardcoded `#333` node-label text color, illegible against the dark theme's canvas. Now reads the active theme's CSS variables at render time.
  - Verified: `python run.py` boots clean, all main routes (`/dashboard`, `/notes/`, `/garden/`, `/notes/<id>`, `/search/`, `/insights`) return 200 for a logged-in user, static CSS/JS serve fine.
  - Ran `pytest tests/`: 5 passed / 9 failed — all 9 failures are the pre-existing `app`-fixture-scope bug (see "Test suite is broken" above) or one unrelated flash-message assertion; none touch templates/CSS/JS. No regressions from this pass.
  - Uncommitted at time of writing — check `git log` for whether/how this landed.

- **2026-09-18** — Read-only audit of full repo state (no code changed). Findings:
  - **Branch state:** `main` == `origin/main` at `ef797c7`. `feature/frontend-polish` is 2 commits ahead (`908138b` pins, `2c05a13` UI redesign), local-only, strictly ahead → fast-forward mergeable. Working tree clean.
  - **`origin/feature/garden-growth-stages` exists remotely** at `1697ae4` ("Add growth-stage plant icons"), with no local branch. Adds `app/services/growth_service.py`, four `app/static/img/garden/*.svg`, `tests/test_growth_service.py`, and changes `garden/routes.py` + `garden/index.html`. **Never fetched or run locally — completely untested here.**
  - **Test suite actual result:** `pytest tests/ -q` → **8 failed, 6 passed** (pytest 9.1.1). 7 failures are the `app`-fixture-shadowing bug (`AttributeError: 'FixtureFunctionDefinition' object has no attribute 'app_context'`); 1 is the unrelated `test_register_duplicate_email` flash assertion. Earlier log entry said 5/9 — count drifts with pytest version, root causes unchanged. `pytest` still absent from `requirements.txt`.
  - **FIX_PLAN FIX-001..004 verified genuinely fixed** in code (CSRF init at `app/__init__.py:4,12,28`; threshold 0.45 at `similarity_service.py:8`; zero `| safe` in templates). FIX-005 only **partial** — unused imports gone, duplicate functions remain.
  - **All REM-001..007 confirmed NOT FIXED.** Garden filter checkboxes (`garden/index.html:36-61`) still have zero JS handlers. `extensions.py` still has zero importers. Two `class Pagination` at `search_service.py:72` and `:112`. `cosine_similarity` at `search_service.py:8` + `similarity_service.py:13`.
  - **New findings not in any doc:** `extract_keywords` duplicated with *different defaults* (`keyword_service.py:19` max=5 vs `similarity_service.py:135` max=10) — behavior diverges by import path. `load_dotenv()` is called **nowhere** (`python-dotenv` is a dep, `.env.example` exists) so every env var silently uses its hardcoded default. No `LICENSE`, no `CONTRIBUTING.md`, no migrations.
  - **`docs/DATABASE_AUDIT.md` is also stale** (previously only CURRENT_PROJECT_INVENTORY was flagged): uses wrong `note1_id`/`note2_id` naming, claims an `embedding_generated` column that isn't in `models.py`, and claims `notes.category` is indexed when `models.py:37` has no `index=True`. Its 94%-accuracy relationship table describes embedding-based scores, but embeddings are dormant — those numbers don't reflect a fresh run.
  - Security items re-confirmed present, all pre-existing: `SECRET_KEY` defaults to literal `'dev-secret-key'` (`app/__init__.py:18`) and that default is what actually runs since dotenv is never loaded; `debug=True` hardcoded (`run.py:22`); embeddings stored/loaded via `pickle` (`embedding_service.py:35,57`).
  - Recommended next order: fix test fixtures + add `pytest` to requirements → merge `feature/frontend-polish` → security pass → dedupe services → decide embeddings story → evaluate the remote growth-stages branch.

When you make further changes, add a dated entry above instead of editing history away — this file is a log, not just a snapshot.
