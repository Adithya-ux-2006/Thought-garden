# Thought Garden — Fix Plan (simplified from audit)

Status legend: **[V]** = reproduced by running it in the audit · **[R]** = found by reading code only (confirm before fixing)

---

## Before you start (one-time, ~30 min)

1. Commit or stash the uncommitted `display_tags` filter work.
2. Merge `feature/garden-growth-stages` into `main` first — it touches `garden/routes.py`, which later phases also change. Avoids conflicts.
3. Back up `instance/thought_garden.db` (needed before Phase 1 migrations).
4. Decide 2 things (defaults assumed below):
   - **Deployed publicly?** Assumed **no** (local/dev only). If yes, move Phase 1 security items up into Phase 0.
   - **scikit-learn:** assumed **drop it** (never imported; FTS5 + existing Jaccard fallback cover keyword needs).

---

## Phase map (7 branches, one concern each)

| # | Branch | What it achieves | Effort | Risk |
|---|---|---|---|---|
| 0a | `fix/critical-bugs` | Core features work again | 1 day | Low |
| 0b | `fix/security-and-cleanup` (exists) | Close the real security holes | 1 day | Low |
| 1 | `refactor/foundations` | Clean schema, fast tests, no startup magic | 2–3 days | Medium |
| 2 | `feature/indexer` | Fast search, reliable AI, honest scores | 4–6 days | Medium |
| 3 | `feature/fts-search` | Good search even without the AI model | 2–3 days | Low |
| 4 | `refactor/data-model` | One source of truth for tags/categories | 2–3 days | Medium |
| 5 | `feature/ux-a11y` | Markdown, accessibility, polish | 3–5 days | Low |
| 6 | (parked) | Export, duplicate detection, LLM/RAG | — | — |

**Order rules:** 0a/0b any order → 1 must come before 2, 3, 4 → 2 before 3 and before "why connected" labels in 5.
**Total:** ~14–22 working days.

**Rule for every fix:** write a failing test first, then fix, then confirm it passes.

---

## Phase 0a — `fix/critical-bugs`

| ID | Bug | Fix | File |
|---|---|---|---|
| C1 [V] | Search from the UI returns nothing (form sends `query`, route reads `q`) | Rename form field to `q`; add a test that submits via the **form** path | `forms.py:61`, `search/routes.py:20` |
| C2 [V] | Editing a note discards tag changes | Only pre-fill `form.tags.data` on GET | `notes/routes.py:115` |
| C3 [V] | Some imports hang forever (`"A." + "x"*3000`) | Guarantee progress: `start = max(end - overlap, start + 1)`; add fuzz test | `document_service.py:69-93` |
| C4 [R] | Source filter `markdown`/`text` never matches stored `md`/`txt` | Make stored values and choices identical | `forms.py:67-68`, `document_service.py:131` |
| C5 [R] | "Found N results" shows page size, not total | Use `pagination.total` | `search.html:43` |
| C7 [R] | Dashboard counts archived notes; "documents" counts starter notes | Filter archived; count only pdf/markdown/text | `main/routes.py:20-21` |
| C8 [R] | Suggest API returns archived notes | Filter archived | `search/routes.py:54` |
| C9 [R] | Editing a note with a non-listed category fails validation | Add current value to choices (real fix comes in Phase 4) | `forms.py:44` |

---

## Phase 0b — `fix/security-and-cleanup`

| ID | Issue | Fix | File |
|---|---|---|---|
| S1 | Stored XSS: tag names/titles injected via `innerHTML` | Build panel with `createElement` + `textContent` | `main.js:268-309` |
| S3 [V] | Open redirect via `?next=` | Allow only relative paths (`urlsplit(next).netloc == ''`) | `auth/routes.py:48-50` |
| S4 | Debug on by default; `.env.example` key bypasses guard; guard reads `Config` | Default `FLASK_DEBUG=0`; check `app.config['SECRET_KEY']` after overrides; blank key in `.env.example` | `config.py:22`, `__init__.py`, `.env.example` |
| S7 | Logout is GET; no secure cookie flags | Logout via POST form; set `SESSION_COOKIE_SECURE`/`REMEMBER_COOKIE_*` when not debug | `auth/routes.py:55`, templates, `config.py` |
| S9 | No 413 handler; file-size limit defined twice | Add 413 handler; read size from config only | `__init__.py`, `document_service.py` |
| NFR | Raw exception text shown to users | Generic flash message + log details with request ID | `notes/routes.py:89,221` |

---

## Phase 1 — `refactor/foundations`

- **Schema:** remove `db.create_all()` from app factory; Alembic becomes the only schema source; autogenerate a migration matching models. (Existing DB: back up → `flask db stamp` → `upgrade`.) [R: fresh-DB failure not executed]
- **SQLite pragmas** via engine connect event: WAL, `busy_timeout`, `foreign_keys=ON`.
- **Tests:** `conftest.py` stubs the embedding model globally → no downloads, no real threads (currently ~37s).
- **No startup magic:** move auto-seed and relationship backfill out of `run.py` into CLI commands `flask seed-demo` and `flask reindex`.
- **Starter notes from a JSON fixture**, not copied from the live demo account → kills the S2 cross-user XSS chain.
- **Auth hardening:** lowercase emails + case-insensitive unique index + catch `IntegrityError` (C10 [R]); login rate limit (S5); require current password to change email (S6).
- **Cleanup:** remove dead code (`suggest_tags`* , `get_relationship_explanation`*, `recalculate_all_relationships`, `DocumentUploadForm`, `get_all_relationships`); drop scikit-learn; remove `pickle.loads` fallback after re-saving old blobs (S8).
  \*Keep these two if you want them for Phase 5 (tag suggestions / "why connected").

---

## Phase 2 — `feature/indexer` (biggest payoff)

Fixes: 14.4s first search [V], no graceful AI fallback, thread races, full rescore on every boot, mixed score scales (C6).

- `index_job` table: `note_id, content_hash, status, attempts, model_version`.
- One background worker, started once; loads the model at startup. **Requests never load the model.**
- `indexer.ready` flag → search uses keyword-only until ready, with a UI notice.
- Re-embed only when `content_hash` changes.
- `rebuild_user_graph(user_id)`: numpy top-k over all note vectors (1,000×384 ≈ 2MB, milliseconds), replace edges in one transaction.
- Add `method` column (`embedding` / `keyword`); show "strong / related" instead of fake %.
- Delete `background_indexing.py`, the unbounded `_embedding_cache`, and the incremental edge logic.

---

## Phase 3 — `feature/fts-search`

- SQLite FTS5 table kept in sync by triggers; `bm25()` ranking; `snippet()` highlights.
- Hybrid (FTS + vector via RRF) only when vectors are ready.

## Phase 4 — `refactor/data-model`

- Tags scoped per user: `UniqueConstraint(user_id, name)`, case-normalised, orphans cleaned.
- Categories: one source of truth (table or config) → colours derived in one place (replaces 4 hand-mirrored lists; fixes missing colours, "AI" vs "Artificial Intelligence" dupes, C9 properly).
- Timezone-aware timestamps; drop unused `Note.summary`.

## Phase 5 — `feature/ux-a11y`

- Safe Markdown rendering (markdown-it-py + nh3).
- Show "why connected" on related notes; tag suggestions on create/edit.
- Delete button on note view.
- Theme set in `<head>` (no light flash); error flashes stay until dismissed.
- `aria-label` on icon buttons; connections list view as graph alternative.
- Load vis-network only on garden pages.
- CSP `script-src 'self'` + move inline `onclick`/`onsubmit` into JS.
- Strip history-narrating comments.
- Replace the 4 source-grep tests with 2–3 browser smoke tests (or delete them).

## Phase 6 — parked

Markdown export/backup, duplicate-note detection, re-ranking, LLM/RAG, collaboration. Only after search + connections are trustworthy.

---

## Quick wins (can be done in minutes, all inside 0a/0b)

C1 search param · C2 tag edit · C3 chunker · S1 textContent · S3 safe `next` · S4 debug default · C7 dashboard filter · persistent error flashes · aria-labels
