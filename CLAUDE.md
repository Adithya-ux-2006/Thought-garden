# CLAUDE.md — Thought Garden

Persistent project context. Keep this file current; prefer concise dated entries over repeating old reasoning. Check actual code/model/file tree over stale docs.

## Project

Flask personal notes app with an AI-discovered knowledge graph: register → copy of a 17-note starter garden → create/import notes → similarity scoring → graph (`vis-network`) or hybrid keyword+semantic search.

**Stack:** Flask, Flask-SQLAlchemy, SQLite, Flask-Login, Flask-WTF, sentence-transformers (`all-MiniLM-L6-v2`), scikit-learn/NumPy, PyPDF2, Bootstrap 5, vanilla JS.

## Key layout

```text
run.py                         app entry; auto-seed empty DB; relationship backfill; :5000
config.py                      centralized Config + load_dotenv()
seed.py                        17-note demo seed across 5 categories
app/__init__.py                app factory; CSRF, DB, Login, request IDs/errors, SECRET_KEY validation
app/models.py                  User, Note, Tag, Relationship, NoteEmbedding
app/forms.py                   Flask-WTF forms
app/{auth,notes,garden,search,main}/routes.py
app/services/                  embedding, background indexing, similarity, keyword, search, pagination, document logic
app/templates/errors/          404.html / 500.html
app/templates/ + app/static/   UI/assets
app/static/vendor/             self-hosted Bootstrap 5.3.3, Bootstrap Icons 1.11.3, vis-network 9.1.9, Fraunces, Inter
migrations/                    Flask-Migrate/Alembic baseline (`a1b2c3d4e5f6`)
tests/                         pytest suite (34 tests: app, growth service, garden frontend source guards)
```

## Environment / startup

Python 3.13. Current compatible pins:
```text
scikit-learn==1.5.2
numpy==1.26.4; python_version < "3.13"
numpy==2.1.2; python_version >= "3.13"
```
Older sklearn/numpy pins fail on this machine because Python 3.13 falls back to builds requiring GCC >= 8.4; installed MinGW is 6.3.0. `sentence-transformers` also makes first install slow because it pulls `torch`.

`.env.example` exists; `python-dotenv` is installed and `config.py` calls `load_dotenv()` at import time. All env vars are centralized in `Config` with defaults.

Local verification command:
```text
python run.py
```
Historically verified: clean boot, 17 seeded notes / 28 relationships, `/` and `/auth/login` return 200. Demo account: `demo@thoughtgarden.app` / `demo1234`.

## Current architecture / important behavior

- **Embeddings:** `NoteEmbedding` is a real model relation (`Note.embedding_row`, `cascade='all, delete-orphan'`, deliberately no `passive_deletes=True`). Stored as raw `numpy.tobytes()` / `np.frombuffer()` instead of pickle; old pickle blobs with protocol-2+ signature `0x80` remain backward-readable.
- **Background indexing:** `queue_embedding_generation()` runs embedding generation + relationship rescoring in a background thread after note create/edit and document import; semantic relationships no longer depend on first semantic search.
- **Similarity helpers:** canonical `cosine_similarity` is in `embedding_service.py`; keyword extraction uses the canonical `keyword_service.py` implementation, with the one former max=10 call site pinned explicitly.
- **Search:** `hybrid_search` uses Reciprocal Rank Fusion `1/(60+rank+1)`. Final note query is user-scoped. Sub-search depth is `page * per_page`, floor 50 / cap 1000. Keyword search currently uses `ILIKE '%q%'`; README's SQLite FTS5 claim is not implemented.
- **Pagination:** canonical `SimplePagination` lives in `app/services/pagination.py` and includes `iter_pages()`; semantic search uses it.
- **Relationships:** `note.get_related_notes()` default `min_similarity=0.0`, matching stored threshold 0.45. `update_relationships_for_note()` preserves a pair when the other note independently still wants it. Archive deletes relationships; unarchive recomputes them. Garden/focus filtering avoids dangling edges. Focus traversal is BFS with a seen-pairs set.
- **Garden data:** `/garden/data` and `/garden/api/focus/<id>` supply category color, growth `stage`, `circularImage`, icon URL, pin state, size, etc. Focus computes total connection counts with one aggregate query after BFS.
- **Growth:** `compute_growth_score()` is 50/50 age + connection score; max age 14 days and max connections 6. Stages: `<.25 seed`, `<.5 sprout`, `<.75 sapling`, otherwise tree. A brand-new note cannot become a tree regardless of connection count; ~7 days + 6 connections reaches the tree threshold. `was_recently_watered()` and related tests/constants were removed as dead code.
- **Pinned nodes:** always `circularImage`; pinned ring is gold (`#a57834`) with `borderWidth=5`. `--pinned-color` in CSS must stay byte-identical to the server ring color. Vis selection is disabled with `chosen:false`; app's own neighborhood dimming handles selection.
- **Garden category colors:** server returns `{background,border}` because Flask cannot know client theme. Browser uses dedicated `--category-*` tokens and `.badge-category-*` classes. Do not re-couple categories to Bootstrap semantic colors.
- **Garden UX:** category filters are functional; search autocomplete is debounced (200ms, 2-char minimum); search/loading feedback exists; node highlighting dims unrelated nodes; physics disables after stabilization and the toggle re-syncs; labels scale-hide below 0.8; dark-mode graph labels update live; focus view shares garden styling.
- **Visual system:** current brand is warm cream + deep forest green + pastel category palette. Core light values: background `#F7F4EC`, primary/nav `#193C32`, text `#26332E`, border `#DED9CA`. Categories: AI `#A99BEA`, Cybersecurity `#E58B78`, SE `#6FAF8F`, OS `#D9A441`, Research `#6F9DB5`. Semantic success/warning/danger/info tokens stay separate. Current typography is self-hosted Fraunces + Inter.
- **CSS/HTML:** garden uses `garden.css`; `focus.html` has no duplicated inline style. `style.css` provides app-wide tokens. No external CDN is required; all Bootstrap/icons/vis/fonts are vendored.
- **Security:** `SECRET_KEY` uses the dev fallback only in debug (with warning). With `FLASK_DEBUG=0`, missing or `dev-secret-key` raises `RuntimeError`; real keys start normally. Request IDs are generated/preserved via `X-Request-ID`, included in logs/responses. 404/500 handlers negotiate HTML vs JSON; 500 rolls back DB and does not expose internals. Bootstrap focus rings were explicitly overridden to the forest-green token.
- **Error/logging:** `RequestIDFilter` handles requests and no-request-context logs; standard format includes timestamp/request ID/level/module/message.

## Current known work / caveats

1. **Rate limiting not yet implemented:** next security task; target login, register, and semantic-search endpoints. Make storage configurable; do not assume in-memory storage is suitable for multi-worker production. Integrate 429 responses with existing error handling.
2. **CSP not yet implemented.**
3. **API/data-hardening roadmap remains:** formalize JSON API, input sanitization review, pagination consistency, query optimization, caching, background-job reliability, type hints/docstrings. Configuration centralization, migrations, pytest, structured errors, and SECRET_KEY hardening are done.
4. **Automated coverage gaps:** `chosen:false` and focus-ring styling have source-level guards only (`tests/test_garden_frontend_regressions.py`), not browser tests; pinned-color consistency is still manual-only.
5. **Deferred structural accessibility:** vis-network renders to canvas, so node category/growth meaning is not exposed as normal DOM text/keyboard targets. A real fix likely needs ARIA/live-region support or a parallel accessible list view; not yet implemented.
6. **Open findings from 2026-09-24 full assessment (not yet fixed; work proceeds in user-assigned phases):**
   - Functional bugs: UI search form field name doesn't match the route's query param; note edit discards tag changes; document chunking can fail to terminate on some inputs; first search loads the model in-request (~14s).
   - Security hardening pending: auth redirect handling, client-side rendering of user content, production config defaults, logout method, upload-limit handling. Details tracked outside the repo.
   - Other: search source-filter values don't match stored `source_type`; result count shows page size; suggest API includes archived notes; `db.create_all()` runs alongside Alembic; keyword and cosine scores share one `similarity_score` column, all labelled `semantic`; scikit-learn unused.

## Documentation rules

- `docs/CURRENT_PROJECT_INVENTORY.md` and `docs/DATABASE_AUDIT.md` are stale/historical and contain wrong schema/template claims. Use actual models/file tree as authority.
- `docs/SELF_AUDIT.md`, `FIX_PLAN.md`, and `PROJECT_HISTORY.md` describe earlier debugging; fixes mentioned there (CSRF, 0.45 similarity threshold, XSS `|safe` removal, dark-mode fixes) are already present.
- `docs/ROADMAP.md` items are wishlist unless reflected below.

## Important history / decisions

- **2026-09-18:** Python 3.13 dependency pins fixed (`908138b`); frontend polish introduced the first design system and dark-mode graph-label fix (`2c05a13`). A full audit identified fixture/test issues and security/cleanup work.
- **2026-09-18 hardening pass:** embeddings moved to `NoteEmbedding` + raw bytes; background indexing added; duplicate similarity/pagination/keyword logic consolidated; RRF search adopted; relationship default fixed; dotenv enabled; garden category filters wired; test fixture bug + duplicate-email test fixed. Full suite then 13 passed / 1 deselected (`test_search` required blocked Hugging Face network access). This work was verified but initially had no push access from that cloud session.
- **2026-09-18 `.gitattributes`:** `5d0f2b1`; LF normalized; no content changes after renormalization.
- **2026-09-18 garden/notes correctness:** `c72c4f0` fixed Focus-in-Graph page/API split, BFS focus traversal, dangling edges after archive, and relationship cleanup on archive/unarchive. `ce936e6` fixed editing one note deleting other notes' independently desired relationships; added deterministic regression test. `380a6f4` fixed category dropdown Row-tuple bug. These were live-verified and fully tested.
- **2026-09-18 garden visualization:** `55c1168` added stable physics, category-anchored seeding, zoom label hiding, click dimming, pinned star, theme-aware category/edge colors, full search highlighting, and legend-style category filters. Live Playwright + 16/16 tests; actual visual rendering was checked where available.
- **2026-09-19 search/dead-code:** search loading state + autocomplete added safely via DOM APIs; dashboard `Most Connected` surfaced; redundant `recent_updated` query removed. Live curl + 16/16.
- **2026-09-19 CDN removal:** vendored Bootstrap 5.3.3, Bootstrap Icons 1.11.3, vis-network 9.1.9, Fraunces, Inter; `base.html` now points only to local assets. Curl/live checks passed; browser offline-mode with blocked hosts was not available, so that remains the only unverified presentation edge.
- **2026-09-19 search/insights correctness:** hybrid final query now user-scoped; hybrid fetch depth fixed; SQLite-only `date('now', '-30 days')` replaced by Python datetime cutoff. Full tests + live curl passed.
- **2026-09-19 garden visual passes:** live Playwright verified light/dark + desktop/tablet/phone. Warm cream/forest/pastel rebrand, garden layout hierarchy, toolbar/panel refresh, focus-view parity, responsive styling, category badges, graph label theme refresh, and growth icons were added.
- **Growth icons:** ported from remote `origin/feature/garden-growth-stages` but did NOT wholesale replace `garden/routes.py` because that branch predates current BFS/archive/RRF/color-shape fixes. Four SVGs require explicit `width="64" height="64"`; nodes use `circularImage`. Category color remains separate from growth icon palette.
- **2026-09-19 audit fixes:** `chosen:false` prevents node click from destroying category/pinned colors; Bootstrap `.btn:focus-visible` focus ring now matches forest green; growth `MAX_AGE_DAYS` changed 30→14 so tree is realistically reachable while preserving the 50/50 invariant; `focus.html` inline style removed; `--pinned-color` added; `was_recently_watered()` removed. Browser verification confirmed pinned/non-pinned click behavior, focus ring across variants, growth boundaries, CSS cleanup, and zero console errors. Full suite: 23 passed.
- **Focus-ring testing caveat:** Bootstrap transitions `box-shadow`; computed style read immediately after Tab shows a transient mid-transition value. Wait ~400ms before asserting final focus color. This is documented in CSS.
- **2026-09-24 demo discoverability:** `display_tags` template filter hides tags equal to the note's category on dashboard/list/search (`e9b8d79`); garden toolbar has a read-only growth legend and the ML Fundamentals seed note is backdated 20 days so the demo shows a tree (`7fd5242`); growth boundary + frontend source-guard tests added (`ac88ac6`). 34/34 tests pass. CLAUDE.md condensed to this format.
- **2026-09-20 post-fix audit:** all six fixes independently reverified; no regressions found across Dashboard/Notes/Search/Insights/Garden, themes, filters, search, node interactions, focus view, keyboard traversal, and growth icons. `--pinned-color` and server pin ring matched exactly (`rgb(165,120,52)`). Growth boundary checks: 0-day/1000-connections caps at sapling; 7-day/6-connections reaches tree. Remaining findings are the current caveats above.

## Git / branch safety

- Repo: `https://github.com/Adithya-ux-2006/Thought-garden`
- Historical working branch: `feature/frontend-polish`; later work was pushed to `main`.
- **Remote main is current through `ac88ac6` plus the CLAUDE.md update that follows it.**
- Backend commits already landed and pushed:
  - `34e5934` — `refactor: centralize application configuration`
  - `1943506` — `feat: add structured error handling`
  - `3634305` — `security: enforce production secret key`
- Most recent documented test checkpoint (2026-09-24): **34/34 tests pass**.
- Pre-existing garden/frontend work must not be included in unrelated backend commits. Before committing: inspect `git status --short`, `git diff --stat`, and `git diff`; stage only files for the current task.

## Working conventions

- Prefer small, sequential changes; avoid unrelated refactors.
- Do not re-read/re-explain this file in every task; use it as context and inspect actual code when details matter.
- Add tests when a change needs regression coverage (security, data integrity, nontrivial logic, refactor); not mechanically for every task.
- Verify appropriately before commit/push. If verification fails or unrelated changes appear, stop rather than committing them.
- When adding history, append a concise dated entry; do not rewrite old decisions unless they are explicitly corrected.
