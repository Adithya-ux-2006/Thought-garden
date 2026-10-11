# CLAUDE.md — Thought Garden

Persistent project context. Keep this file current; prefer concise dated entries over repeating old reasoning. Check actual code/model/file tree over stale docs.

## Project

Flask personal notes app with an AI-discovered knowledge graph: register → copy of a 17-note starter garden → create/import notes → similarity scoring → graph (`vis-network`) or hybrid keyword+semantic search.

**Stack:** Flask, Flask-SQLAlchemy, SQLite, Flask-Login, Flask-WTF, sentence-transformers (`all-MiniLM-L6-v2`), NumPy, PyPDF2, Bootstrap 5, vanilla JS.

## Key layout

```text
run.py                         app entry; refuses to start unless schema is at Alembic head; :5000
config.py                      centralized Config + load_dotenv()
app/cli.py                     `flask seed-demo`, `flask reindex`, schema_is_current()
app/data/starter_notes.json    17 starter notes (new-user garden and demo seed)
app/__init__.py                app factory; CSRF, CSP, DB, Login, request IDs/errors, SECRET_KEY validation, template filters
app/models.py                  User, Note, Tag, Relationship, NoteEmbedding, IndexJob
app/forms.py                   Flask-WTF forms
app/{auth,notes,garden,search,main}/routes.py
app/services/                  embedding, indexer, similarity, keyword/tag suggestions, search, markdown, category, pagination, document logic
app/templates/errors/          404.html / 500.html
app/templates/macros/ui.html    empty_state() macro (growth-stage plant + headline + action)
app/services/knowledge_service.py  garden_health / export_garden / duplicate_candidates / summarize_note / make_flashcards (remote, 2026-09-29)
thoughtgarden-src/Thought-garden-main/  Streamlit port (Adithya): self-contained copy with its OWN app/, config.py, tests/, requirements.txt; entry app_streamlit.py
.streamlit/config.toml         Streamlit theme (Phase 4 palette); fonts in thoughtgarden-src/Thought-garden-main/static/fonts/
.devcontainer/                 Codespaces: Python 3.11, runs the Streamlit app on :8501
graphify-out/                  generated knowledge-graph snapshots (remote chore commits; don't edit)
app/templates/ + app/static/   UI/assets
app/static/vendor/             self-hosted Bootstrap 5.3.3, Bootstrap Icons 1.11.3, vis-network 9.1.9, EB Garamond, Inter
migrations/                    Flask-Migrate/Alembic baseline (`a1b2c3d4e5f6`)
tests/                         pytest suite; conftest.py stubs the embedding model; test_browser_smoke.py needs Playwright + Chromium (skips without)
```

## Environment / startup

Python 3.13. Current compatible pins:
```text
numpy==1.26.4; python_version < "3.13"
numpy==2.1.2; python_version >= "3.13"
```
Older numpy pins fail on this machine because Python 3.13 falls back to builds requiring GCC >= 8.4; installed MinGW is 6.3.0. scikit-learn is no longer a direct dependency but is still installed transitively by `sentence-transformers` (resolves to a prebuilt wheel). `sentence-transformers` also makes first install slow because it pulls `torch`.

`.env.example` exists; `python-dotenv` is installed and `config.py` calls `load_dotenv()` at import time. All env vars are centralized in `Config` with defaults.

Local startup (needs `SECRET_KEY` or `FLASK_DEBUG=1` in `.env`):
```text
flask db upgrade      # Alembic is the only schema source; app never calls create_all()
flask seed-demo       # optional: demo@thoughtgarden.app / demo1234, local only
flask reindex         # optional: recompute all relationships
python run.py
```
Streamlit port (run from the repo root so `.streamlit/config.toml` applies; Python 3.10–3.13, tested 3.13.1 on Windows 11):
```text
python -m venv .venv-streamlit && pip install -r thoughtgarden-src/Thought-garden-main/requirements.txt
streamlit run thoughtgarden-src/Thought-garden-main/app_streamlit.py --server.address 127.0.0.1
```
Gate password `demo1234` (override `STREAMLIT_GATE_PASSWORD` or `gate_password` in `.streamlit/secrets.toml`). Root `.env`'s relative `DATABASE_URL` resolves to the port's own `thoughtgarden-src/Thought-garden-main/instance/thought_garden.db` — separate from the Flask DB. Base env ~392 MB; `sentence-transformers` is optional (keyword fallback without it; +~540 MB torch + model). Without `--server.address 127.0.0.1` Streamlit listens on all interfaces.

Existing DBs: back up `instance/thought_garden.db`, then `flask db upgrade` (a pre-migrations DB without `alembic_version` needs `flask db stamp a1b2c3d4e5f6` first). The real dev DB was at `a1b2c3d4e5f6` on 2026-09-24; a backup is at `instance/thought_garden.pre-phase1-2026-09-24.db`.

## Current architecture / important behavior

- **Embeddings:** `NoteEmbedding` is a real model relation (`Note.embedding_row`, `cascade='all, delete-orphan'`, deliberately no `passive_deletes=True`). Stored as raw float32 bytes. Never unpickled: migration `c4d8a2b6e9f1` deletes legacy pickled rows and any unreadable blob is treated as missing and regenerated.
- **Background indexing:** `indexer.enqueue(note)` upserts an `IndexJob`; one worker per process (`indexer.start_worker`, skipped under `TESTING`) loads the model at startup, re-embeds only on `content_hash` change, then rebuilds the user's graph. Tests call `indexer.process_pending(app)` directly.
- **Similarity helpers:** canonical `cosine_similarity` is in `embedding_service.py`; keyword extraction uses the canonical `keyword_service.py` implementation, with the one former max=10 call site pinned explicitly.
- **Search:** `hybrid_search` uses Reciprocal Rank Fusion `1/(60+rank+1)`. Final note query is user-scoped. Sub-search depth is `page * per_page`, floor 50 / cap 1000. Keyword side is SQLite FTS5 (bm25 + escaped `snippet()`); vectors join via RRF only when `indexer.ready`.
- **Pagination:** canonical `SimplePagination` lives in `app/services/pagination.py` and includes `iter_pages()`; semantic search uses it.
- **Relationships:** `rebuild_user_graph(user_id)` recomputes a user's edges in one pass; each row has `method` (`embedding`/`keyword`) and is shown via `relationship_label()` ("Strong match"/"Related"), never a raw %. `note.get_related_notes()` returns `(other_note, Relationship)` pairs. "Why connected" is `explain_connection(note, other, rel)`: describes an existing edge (shared tags/keywords/category) without rescoring. Archive deletes relationships; unarchive recomputes them. Garden/focus filtering avoids dangling edges. Focus traversal is BFS with a seen-pairs set.
- **Garden data:** `/garden/data` and `/garden/api/focus/<id>` supply category color, growth `stage`, `circularImage`, icon URL, pin state, size, etc. Focus computes total connection counts with one aggregate query after BFS.
- **Growth:** `compute_growth_score()` is 50/50 age + connection score; max age 14 days and max connections 6. Stages: `<.25 seed`, `<.5 sprout`, `<.75 sapling`, otherwise tree. A brand-new note cannot become a tree regardless of connection count; ~7 days + 6 connections reaches the tree threshold. `was_recently_watered()` and related tests/constants were removed as dead code.
- **Pinned nodes:** always `circularImage`; pinned ring is gold (`#a57834`) with `borderWidth=5`. `--pinned-color` in CSS must stay byte-identical to the server ring color. Vis selection is disabled with `chosen:false`; app's own neighborhood dimming handles selection.
- **Garden category colors:** server returns `{background,border}` because Flask cannot know client theme. Browser uses dedicated `--category-*` tokens and `.badge-category-*` classes. Do not re-couple categories to Bootstrap semantic colors.
- **Garden UX:** category filters are functional; search autocomplete is debounced (200ms, 2-char minimum); search/loading feedback exists; node highlighting dims unrelated nodes; physics disables after stabilization and the toggle re-syncs; labels scale-hide below 0.8; dark-mode graph labels update live; focus view shares garden styling.
- **Visual system:** current brand is warm cream + deep forest green + pastel category palette. Core light values: background `#F7F4EC`, primary/nav `#193C32`, text `#26332E`, border `#E2DCCD` (form controls `--border-strong` `#87907F`). Categories: AI `#A99BEA`, Cybersecurity `#E58B78`, SE `#6FAF8F`, OS `#D9A441`, Research `#6F9DB5`. Semantic success/warning/danger/info tokens stay separate. Supporting palette: sage `#78917C`, sand `#D5BFA0`, terracotta `#C77D69` (accent); raw sage/terracotta are decorative only, text uses `--sage-text`/`--terracotta-text`. Typography: self-hosted EB Garamond (headings, weight 400–500; Apple Garamond is not web-licensed) + Inter. Category badge classes live in `style.css` (used app-wide).
- **Motion:** tokens `--dur-fast/base/enter/ambient` + `--ease-*` in `style.css`; `--transition` names properties (never `all`). Entrances use `animation-fill-mode: backwards` and individual `translate`/`scale` (no lingering transform → no stacking-context/Popper conflicts). Global `prefers-reduced-motion` override at end of `style.css`; JS checks `prefersReducedMotion()`. Garden: hover previews neighbourhood (0.4 dim), click/search pin it (0.12 dim, same end values as before), ~180ms tween skipped above 600 nodes+edges or under reduced motion; notes new since last visit (localStorage `tg.gardenSeen.<user>`) grow in once; canvas nodes never animate continuously — only legend/empty-state SVGs sway. No CSS view transitions (Chromium threw a pageerror the smoke test catches).
- **CSS/HTML:** garden uses `garden.css`; `focus.html` has no duplicated inline style. `style.css` provides app-wide tokens. No external CDN is required; all Bootstrap/icons/vis/fonts are vendored.
- **Security:** `SECRET_KEY` uses the dev fallback only in debug (with warning). With `FLASK_DEBUG=0`, missing or `dev-secret-key` raises `RuntimeError`; real keys start normally. Request IDs are generated/preserved via `X-Request-ID`, included in logs/responses. 404/500 handlers negotiate HTML vs JSON; 500 rolls back DB and does not expose internals. Bootstrap focus rings were explicitly overridden to the forest-green token.
- **CSP:** `script-src 'self'`, no `unsafe-inline`/`unsafe-eval`. No inline scripts, `on*` handlers or `style=""` anywhere (tested); page data goes through `<script type="application/json">` blocks, events are wired in `main.js`. `style-src` allows only `'self'` + `VIS_NETWORK_STYLE_HASHES` (the `<style>` blocks vis-network 9.1.9 injects, incl. an empty one) — **recompute if vis is upgraded**. `img-src` allows `https:` for Markdown images. vis-network loads only on `/garden/` and `/garden/focus/*` (landing hero is static SVG).
- **Markdown/XSS:** note content renders via the `|markdown` filter (`markdown_service.py`: markdown-it-py with `html=False`, then nh3 allowlist, http/https/mailto only). JS builds all user text with `textContent`; templates never use `|safe`.
- **UX/a11y:** theme set by blocking `theme-init.js` in `<head>`; danger/warning flashes persist, others auto-dismiss (`data-autodismiss`); icon-only controls have `aria-label`s; `/garden/list` is the accessible graph alternative; tag suggestions (`POST /notes/api/suggest-tags`, CSRF via `X-CSRFToken`) only suggest the user's existing tags.
- **Error/logging:** `RequestIDFilter` handles requests and no-request-context logs; standard format includes timestamp/request ID/level/module/message.

## Current known work / caveats

1. **Rate limiting:** failed logins are limited per client IP (`LOGIN_MAX_FAILED_ATTEMPTS`/`LOGIN_LOCKOUT_SECONDS`, in-process state, so single-process only; uses `request.remote_addr`, no proxy support). Register and semantic search are not rate limited.
2. **CSP caveats:** `img-src https:` lets note images load third-party pixels; vis style hashes must be recomputed on any vis-network upgrade (browser smoke test fails on violations).
3. **API/data-hardening roadmap remains:** formalize JSON API, input sanitization review, pagination consistency, query optimization, caching, background-job reliability, type hints/docstrings. Configuration centralization, migrations, pytest, structured errors, and SECRET_KEY hardening are done.
4. **Browser coverage is optional:** `chosen:false`, dimming, focus ring, CSP, flashes, delete confirm, tag chips etc. are covered by `tests/test_browser_smoke.py` (real Chromium, mutation-verified), which skips silently without Playwright. Pinned-color consistency is still manual-only.
5. **Graph canvas accessibility:** vis canvas itself isn't keyboard/screen-reader accessible; mitigated by `/garden/list`, a visually-hidden text alternative, and `role=img`.
6. **Phase 6 partly landed (remote, 2026-09-29):** JSON export (`/export`), duplicate candidates (`/notes/duplicates`), study summary/flashcards. Still parked (`FIX_PLAN.md`): Markdown export/backup, re-ranking, LLM/RAG, collaboration.

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
- **2026-09-24 Phases 0a/0b/1 (`fix/critical-bugs`, `fix/security-and-cleanup`, `refactor/foundations`):** 0a fixed UI search, tag edits, chunker hang, filters/counts; 0b hardened panel rendering, login redirects, debug/secret defaults, logout (POST+CSRF), cookies, upload limit, error messages. Phase 1: Alembic-only schema (+ email-normalization and pickled-embedding migrations), SQLite pragmas (FK/WAL/busy_timeout), startup magic replaced by `flask seed-demo`/`flask reindex`, starter garden from a JSON fixture (no longer copied from the demo account), case-insensitive emails, login rate limit, password required to change email, dead code + scikit-learn removed. Migrations verified on a copy of the real DB.
- **2026-09-26 Phases 2–4 (`a163074`, `feature/fts-search`):** indexer + `IndexJob` queue (model never loaded in-request), `rebuild_user_graph`, `Relationship.method`, FTS5 search, per-user tags, single category source, tz-aware timestamps.
- **2026-09-26 Phase 5 (`feature/ux-a11y`):** safe Markdown, "why connected", tag suggestions, delete on note view, head theme init, persistent error flashes, aria-labels, `/garden/list`, vis scoped to garden pages (landing hero → static SVG), CSP, inline handlers moved to JS, history comments stripped. The 4 source-grep tests were replaced by 12 Playwright smoke tests (each mutation-verified). Full suite 243 passed, 0 skipped. No schema change.
- **2026-10-11 Phase 4 visual identity (`f2770d3`):** botanical editorial redesign: EB Garamond replaces Fraunces, sage/sand/terracotta tokens, motion system, solid navbar with animated active indicator, signed-out brand header, editorial note view, composer forms, unified insight cards, botanical empty states, landing growth path (replaced the empty `#featureGraph` box), garden hover/search emphasis + growth entrance + panel transitions. 243 passed; live Playwright on a DB copy: 17 pages × desktop/tablet/phone × light/dark, zero overflow/console errors; contrast AA verified. Caveat: headless Chromium sometimes stalls the very first frame of a new browser (looks like a blank/unstyled page) — warm up before screenshots.
- **2026-10-11 merge + verification (`cdbd01b`, `dd55f8e`):** merged remote `origin/main` (Adithya, 2026-09-20..30: Streamlit port, `/health`, `/export`, `/notes/duplicates`, `/notes/<id>/study`, knowledge_service, devcontainer, graphify-out) — treated as correct, logic untouched. Clean auto-merge; Health nav link given the Phase 4 indicator. Restyled health/duplicates/study, wrapped notes-header buttons on phones, themed Streamlit via `.streamlit/config.toml`. Verified: `pytest tests` 268 passed; port's own tests 23 passed (run from its dir); Streamlit clean-venv install on 3.13.1, all 6 pages 0 exceptions, notes + keyword linking + garden graph work. Known in remote work (left as-is): Streamlit sidebar lists pages twice (st.navigation + page_link loop); sidebar note count cached until restart; root `pytest` collects the port's tests and errors — use `pytest tests`.
- **2026-09-20 post-fix audit:** all six fixes independently reverified; no regressions found across Dashboard/Notes/Search/Insights/Garden, themes, filters, search, node interactions, focus view, keyboard traversal, and growth icons. `--pinned-color` and server pin ring matched exactly (`rgb(165,120,52)`). Growth boundary checks: 0-day/1000-connections caps at sapling; 7-day/6-connections reaches tree. Remaining findings are the current caveats above.

## Git / branch safety

- Repo: `https://github.com/Adithya-ux-2006/Thought-garden`
- Historical working branch: `feature/frontend-polish`; later work was pushed to `main`.
- **Remote `main` is current through `dd55f8e` plus the CLAUDE.md update that follows it (2026-10-11). Adithya also pushes to `main` — always `git fetch` before pushing; merge (no rebase/force) if behind.**
- Backend commits already landed and pushed:
  - `34e5934` — `refactor: centralize application configuration`
  - `1943506` — `feat: add structured error handling`
  - `3634305` — `security: enforce production secret key`
- Phase branches: `fix/critical-bugs`, `fix/security-and-cleanup` pushed; `feature/ux-a11y` (Phase 5, on top of `a163074` Phases 1–4) pushed 2026-09-26; all merged into `main` (local branches are stale and can be deleted).
- Most recent documented test checkpoint (2026-10-11, `main`): `pytest tests` 268 passed (Playwright present).
- Pre-existing garden/frontend work must not be included in unrelated backend commits. Before committing: inspect `git status --short`, `git diff --stat`, and `git diff`; stage only files for the current task.

## Working conventions

- Prefer small, sequential changes; avoid unrelated refactors.
- Do not re-read/re-explain this file in every task; use it as context and inspect actual code when details matter.
- Add tests when a change needs regression coverage (security, data integrity, nontrivial logic, refactor); not mechanically for every task.
- Verify appropriately before commit/push. If verification fails or unrelated changes appear, stop rather than committing them.
- When adding history, append a concise dated entry; do not rewrite old decisions unless they are explicitly corrected.
