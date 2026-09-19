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

- **2026-09-18** — Security/cleanup pass ported onto `feature/frontend-polish` (uncommitted on top of `ddbac80` as of this writing — cloud session has no push access to origin, see below). All changes verified with `python run.py` boot + route smoke test and `pytest tests/`.
  - **`note_embeddings` moved from raw SQL to a real `NoteEmbedding` model** (`app/models.py`), wired via `Note.embedding_row` (`cascade='all, delete-orphan'`, deliberately *without* `passive_deletes=True` — an earlier attempt with it silently broke cascade delete, verified by direct DB check before removing it).
  - **Embeddings switched from `pickle` to raw `numpy.tobytes()`/`np.frombuffer()`** (`embedding_service.py`), closing the unpickling-untrusted-DB-content code-exec surface called out above. Backward-compatible: old pickle blobs (protocol 2+ signature byte `0x80`) still decode.
  - **Embeddings are no longer dormant.** `queue_embedding_generation()` (new `app/services/background_indexing.py`) runs embedding generation + relationship rescoring in a background thread, fired from `notes/create`, `notes/edit`, and document import. A note's real semantic relationships now show up shortly after save instead of only after someone runs the first semantic search.
  - **Deduped `cosine_similarity`** (canonical copy now in `embedding_service.py`) and **`Pagination`** (new `app/services/pagination.py`, `SimplePagination` with `iter_pages()` — fixes the confirmed live crash where `semantic_search`'s copy lacked it and `search/search.html` calls it). `extract_keywords` duplication resolved by importing the canonical `keyword_service` version; the one call site that relied on the old default (`max_keywords=10` in `get_relationship_explanation`) pins it explicitly so behavior didn't silently change.
  - **`hybrid_search` combination logic replaced** with Reciprocal Rank Fusion (`1/(60+rank+1)`) instead of the unbounded `1.0 - rank*0.02` fudge.
  - **`note.get_related_notes()` default `min_similarity` changed 0.7 → 0.0** — matches actual storage threshold (0.45); the 0.7 default was landmine-only since every caller already overrode it.
  - **`load_dotenv()` now actually called** (`app/__init__.py`). `SECRET_KEY` fallback now logs a warning instead of silently using the insecure default. `run.py` debug mode now reads `FLASK_DEBUG` env var (still defaults on, for local dev). `.env.example` `SIMILARITY_THRESHOLD` fixed 0.7 → 0.45.
  - **Garden category filter checkboxes wired up** (`main.js`: `applyGardenCategoryFilters()`, checkbox class added in `garden/index.html`) — REM-001 fixed, verified via pure-JS logic simulation.
  - **Test suite fixture-scoping bug fixed** (`tests/test_app.py`): 7 tests took `app` as a bare module reference instead of the pytest fixture — added `app` as an explicit parameter to each. Also fixed `test_register_duplicate_email`, which wasn't actually a broken assertion — `register()` auto-logs-in on success and redirects any already-authenticated request to `/dashboard` before the duplicate-email check runs, so the test needed a `logout` between the two register calls to actually exercise that path.
  - **Full suite result: 13 passed, 1 deselected** (`test_search` — needs network access to `huggingface.co`, blocked in this environment; not run here, should pass in an unrestricted environment). Zero regressions from tasks in this pass.
  - `pytest` still not added to `requirements.txt` — recommended, not yet done.
  - Nothing in this entry has been committed or pushed from this session — this cloud session has no push access to `origin/Adithya-ux-2006/Thought-garden` (git proxy returns 403). Needs to land via the authorized terminal session, as with prior entries.

- **2026-09-18** — `.gitattributes` added (`5d0f2b1`) to normalize line endings to LF in-repo; renormalize produced zero content changes (the local `core.autocrlf=true` was already handling CRLF-on-disk transparently, just not enforced for other clones/OSes before this).

- **2026-09-18** — Series of garden/notes bug fixes, each verified with a real HTTP round-trip (login via curl, not just unit tests) plus the full suite, and each committed+pushed to `main` separately:
  - **`c72c4f0`** — "Focus in Graph" button was a dead link to a JSON API endpoint (`garden.focus`), so clicking it on a note page dumped raw JSON. Split into a real page route (new `garden/focus.html`, wiring up `main.js`'s previously-unused `initFocusGraph`/`renderFocusGraph`) plus `/garden/api/focus/<id>` for the JSON. Also rewrote `focus_data()` as a level-by-level BFS (was one query per node recursively — 100+ queries at depth 2) with a seen-pairs set to stop duplicate edges. Same commit also fixed the garden breaking when notes are archived: `/garden/data` and the focus route now require *both* edge endpoints to be in the visible/resolved node set (archiving left relationship rows in place, so vis-network got edges pointing at nodes that no longer existed), and `notes.archive()` now deletes the note's relationships on archive / calls `update_relationships_for_note()` on unarchive instead of just flipping the flag.
  - **`ce936e6`** — Editing one note was silently deleting *other* untouched notes' relationships. Root cause: `update_relationships_for_note()` deleted any existing relationship not in the edited note's own recomputed top-N, even when that relationship existed because the *other* note ranked it highly. Fixed by checking, before deleting, whether the other note's own top-N (recomputed on its own terms) still wants the pair — only delete when neither side wants it. Chose this over an `owner_note_id` column (would need a migration this project has none of, and wouldn't be sufficient alone) or never-delete-on-rescore (stops cleaning up pairs that genuinely no longer qualify). Trade-off: a note's total relationship count is still its own top-N *plus* whatever else independently picked it, not a hard cap — inherent to respecting the other side's preference. Added `test_editing_note_does_not_destroy_other_notes_connections` (9 notes, controlled 2D embeddings for determinism, no tag/keyword fuzziness or DB-ordering ties); confirmed it fails against the pre-fix code and passes with the fix.
  - **`380a6f4`** — Search page category dropdown was built from unpacked SQLAlchemy Row tuples (`[(c, c) for c in query(...).all()]`), so it rendered literal `('AI',)` text and `category=('AI',)` matched no note — filter silently no-op'd. Fixed by unpacking `c[0]`. Tag choices on the next line were already correct (`Tag.query` returns ORM instances, not Rows).
  - All three verified live: `pytest` full suite passing throughout (16/16 by the end), plus curl-driven login + route checks (dangling-edge JSON inspection, category-filtered result counts against known seed data, etc.) — not just unit tests.

- **2026-09-18** — Garden visualization UX pass, committed+pushed as **`55c1168`**: physics now disables itself on `stabilizationIterationsDone` (was running forever) with the Physics toggle re-syncing to reflect that, so re-checking it re-energizes the graph. Nodes seeded at category-anchored ring positions before physics runs, for visible per-category neighbourhoods — chose this over vis-network's clustering API since clustering merges nodes into meta-nodes and would've complicated click handling, neighbourhood-highlight, and search. Labels hide below zoom scale 0.8 and reappear above it. Clicking a node now dims every non-connected node/edge (converted to low-alpha RGBA client-side) and restores on deselect/background click. `is_pinned` now renders as a star shape with a heavier border (previously received from the server but completely ignored). `get_category_color()` (`app/garden/routes.py`) now derives from the design system's dark-theme token values instead of leftover Tailwind defaults. The hardcoded per-edge `color` dict in both `data()` and `focus_data()` was removed — a per-edge color in vis-network overrides the *global* themed option entirely, which was silently defeating the dark-mode-aware edge color `main.js` computes from CSS variables. `searchNode()` now highlights every match (not just the first) and reports a "no notes match" message instead of doing nothing. Existing filter checkboxes relabeled as a legend (no new component needed — the badges already visually match node colors once both draw from the same tokens). Verified: clean import, `node --check` on the JS, full suite 16/16, `/garden/data` and `/garden/api/focus/<id>` payload-inspected (zero edges carry a `color` key, 5 categories map to new hex values, `is_pinned` unaffected, node/edge key shapes otherwise unchanged) — actual visual rendering (clustering tightness, dim/highlight animation, dark-mode contrast) not eyeballed in a browser, no browser tool available this session.

- **2026-09-19** — Search loading feedback + resolved two pieces of dead code, all in one pass.
  - **Search now shows loading feedback.** `search/search.html`'s form got `data-ai-processing` + `data_loading_text="Searching your garden..."` on the submit button — same mechanism `notes/create.html`/`edit.html` already use. Matters because `semantic_search()` (`search_service.py`) calls `get_model()`/`model.encode()` inside the request with zero prior indication anything's happening; first search after a restart (or first ever, on a fresh machine) blocks for many seconds loading/downloading the sentence-transformers model.
  - **`/search/api/suggest` wired into the search box as real autocomplete** (chose this over deleting it — already written, genuinely useful). Debounced fetch (200ms, 2-char minimum) in a new `initSearchAutocomplete()` in `main.js`. Deliberately built with `createElement`/`textContent`, not an innerHTML template string with interpolated values — note titles/categories are user content, and this project already had one XSS incident from exactly that mistake (`| safe` in note view, see SELF_AUDIT.md). Note: `showNotePanel()` in the same file (garden side panel) still has that innerHTML-with-interpolation pattern for tags/connections — pre-existing, not touched by this pass, flagged for a future cleanup.
  - **`dashboard()`'s `most_connected` query surfaced** as a new "Most Connected" card on the dashboard (chose over deleting — already written, fits the product). **`recent_updated` query deleted** (chose over surfacing — genuinely redundant with the already-shown "Recently Added" panel for a single-user app with a handful of notes; a second recently-touched list would've just been clutter, no natural home in the layout).
  - Verified: clean import, `node --check`, full suite 16/16, then live via curl: search page renders `data-ai-processing`/`data-loading-text`/`id="query"`/`#searchSuggestions` correctly, `/search/api/suggest?q=machine` returns real results in the shape the JS expects (previously unreachable, confirmed dead before this), dashboard renders "Most Connected" with real counts and correct pluralization, `recent_updated` fully gone from both the route and the render.

- **2026-09-19** — Removed the app's hard dependency on 4 external CDNs (jsdelivr, unpkg, fonts.googleapis.com, fonts.gstatic.com). Reproduced the failure first: with those hosts blocked, Bootstrap's JS never loads so dropdowns render permanently expanded (note-card menus become an unusable wall of buttons), all icons vanish, and the garden throws `vis is not defined` and shows nothing — no user-facing error in any case. Fixed by vendoring everything into the repo:
  - **`app/static/vendor/bootstrap/5.3.3/`** — `bootstrap.min.css` + `bootstrap.bundle.min.js` (npm-packed from `bootstrap@5.3.3`).
  - **`app/static/vendor/bootstrap-icons/1.11.3/font/`** — `bootstrap-icons.min.css` + its `fonts/` dir (woff/woff2). Left the CSS's relative `url('fonts/bootstrap-icons.woff2')` untouched — it resolves correctly as long as the two stay siblings, which they do here.
  - **`app/static/vendor/vis-network/9.1.9/`** — `vis-network.min.js` (from the package's `standalone/umd/` build, same one unpkg was serving).
  - **`app/static/vendor/fonts/`** — self-hosted Fraunces + Inter, chosen over keeping the Google Fonts CDN link since the whole point was killing CDN dependencies, not 3 out of 4. Fetched the real `@font-face` CSS from `fonts.googleapis.com` with a Chrome UA to get the actual `fonts.gstatic.com` woff2 URLs, then downloaded them directly — both are variable fonts, so despite the original CSS declaring 3 separate `font-weight` blocks for Fraunces (500/600/700) and 4 for Inter (400/500/600/700), each family resolves to exactly **one** woff2 file covering the whole weight range (`font-weight: 500 700` / `400 700` range syntax) — only 2 font files vendored, not 7. Only the `latin` unicode-range subset was kept (dropped cyrillic/greek/vietnamese-only blocks) since this is an English-only app; `style.css`'s existing fallback stacks (`Georgia`/`Times New Roman`/serif for Fraunces, system-font stack for Inter) were already solid so no changes needed there.
  - All version numbers are in the path (`.../bootstrap/5.3.3/...` etc.) — bump the directory name, not the file, on future upgrades.
  - `app/templates/base.html` rewritten to load all of the above via `url_for('static', ...)` — zero `<link>`/`<script>` tags pointing at an external host anywhere in the app now (repo-wide grep for `jsdelivr|unpkg|googleapis|gstatic` after the change returns only this CLAUDE.md entry).
  - Verified live: booted `python run.py`, curled every vendored asset path directly (all 200), logged in as the demo user and confirmed `/garden/` renders with `src`/`href` pointing at the new `/static/vendor/...` paths and no CDN references anywhere in the rendered HTML. Did not verify in an actual browser with devtools offline mode / blocked hosts — no browser tool available this session; the curl-level check (every asset the templates reference now resolves under `/static/`, and the previous jsdelivr/unpkg/googleapis URLs are gone from the rendered output) is what's actually been confirmed. If picking this back up, a real offline-mode browser check of dropdowns/icons/garden rendering is the one thing still worth doing.
  - `app/static/vendor/` is committed to the repo (not gitignored) — it's meant to be there, not fetched at build time.

- **2026-09-19** — Three small correctness fixes in search/insights, all low-risk, none behavior-changing for the common case:
  - **`hybrid_search`'s final `Note.query.filter(Note.id.in_(sorted_ids))`** (`search_service.py`) had no `user_id` filter. Not exploitable today — `sorted_ids` only ever contains IDs that came out of `keyword_search`/`semantic_search`, which are both already user-scoped — but it was one upstream regression away from a cross-user data leak with zero defence in depth. Added `Note.user_id == user_id` to the same query.
  - **`hybrid_search` fetched a hardcoded `per_page=50` from each of the two sub-searches** before merging via RRF, so anything past ~100 combined hits was silently unreachable and the reported total was wrong for larger result sets. Fixed properly rather than just documenting the cap: fetch depth now scales as `page * per_page` (floor 50, cap 1000). This is cheap at this cap because `semantic_search`'s dominant cost — encoding the query + scoring every stored embedding — doesn't scale with `per_page` at all (it already computes similarity against the full set before slicing); only `keyword_search`'s DB `LIMIT` grows, which is negligible at this size.
  - **`main/routes.py`'s `insights()` used `func.date('now', '-30 days')`** for the "Growing Topic" stat — a SQLite-only function that would silently break (or silently return wrong results, not even error) if this ever moved to Postgres/MySQL. Replaced with a Python-computed `datetime.utcnow() - timedelta(days=30)` compared against `Note.created_at`, which is backend-agnostic.
  - Verified: full pytest suite (16 passed), then live via curl as the demo user — `/search/?q=network&mode=hybrid` on both page 1 and page 2 render real result cards, `/insights` renders "Growing Topic: AI, 6 new notes this month" correctly off the new cutoff logic.

When you make further changes, add a dated entry above instead of editing history away — this file is a log, not just a snapshot.
