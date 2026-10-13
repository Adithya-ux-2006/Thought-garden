# Graph Report - thoughtgarden  (2026-10-13)

## Corpus Check
- 173 files · ~177,628 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2788 nodes · 5869 edges · 154 communities (125 shown, 29 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 244 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2173bdca`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app/forms.py
- app/models.py
- Thought-garden-main/tests/test_app.py
- Database Tables (5, all real SQLAlchemy models — see `app/models.py`)
- test_ux_a11y.py
- flowers.py
- What You Must Do When Invoked
- PEAS Description - Thought Garden Intelligent Agent
- compute_growth_stage
- garden-graph.js
- Thought Garden Architecture
- Thought Garden Roadmap
- Thought Garden Self Audit
- 🌱 Thought Garden
- Thought Garden — Database Audit
- Tables
- Thought Garden — Project History
- Route Definitions
- graphify reference: extra exports and benchmark
- Thought Garden Fix Plan
- graphify reference: query, path, explain
- Thought Garden UML Flows
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- extraction-spec.md
- app/notes/routes.py
- app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js
- tg_ui/static/vendor/vis-network/9.1.9/vis-network.min.js
- 2_Notes.py
- app/static/vendor/vis-network/9.1.9/vis-network.min.js
- NoteEmbedding
- Tag
- cs
- remove
- tg_ui/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js
- test_security.py
- remove
- create_app
- A
- A
- streamlit_notes_ops.py
- Database Tables (5, all real SQLAlchemy models — see `app/models.py`)
- Thought-garden-main/app/static/js/main.js
- xt
- cs
- qi
- qi
- Bt
- streamlit_auth.py
- Jn
- Thought Garden Architecture
- Thought Garden Self Audit
- app/main/routes.py
- streamlit_ui.py
- .hide
- xt
- g
- yd
- Kv
- Thought-garden-main/app/services/similarity_service.py
- Ks
- app/services/__init__.py
- ii
- Thought-garden-main/app/models.py
- streamlit_garden_ops.py
- Note
- g
- User
- Tables
- 🌱 Thought Garden
- Relationship
- test_auth.py
- Thought Garden — Project History
- Route Definitions
- Thought Garden — Database Audit
- PEAS Description - Thought Garden Intelligent Agent
- ao
- tg_ui/static/js/main.js
- Non-Functional Requirements (NFR)
- cn
- Non-Functional Requirements (NFR)
- test_critical_bugs.py
- CLAUDE.md — Thought Garden
- CLAUDE.md — Thought Garden
- Ks
- migrations/env.py
- Thought Garden Fix Plan
- Thought Garden Roadmap
- Thought-garden-main/migrations/env.py
- Contributing to Thought Garden
- Thought-garden-main/app/services/growth_service.py
- Contributing to Thought Garden
- Extension Points
- rb
- Extension Points
- Installation
- SimplePagination
- Installation
- Version 2.0 (Medium-term)
- Version 3.0 (Long-term)
- Thought-garden-main/app/services/keyword_service.py
- Version 2.0 (Medium-term)
- Version 3.0 (Long-term)
- app/garden/routes.py
- Thought-garden-main/config.py
- test_markdown.py
- Jn
- Thought-garden-main/app/notes/routes.py
- 1_Dashboard.py
- test_browser_smoke.py
- yd
- app/services/embedding_service.py
- tests/test_app.py
- Bt
- test_migrations.py
- app_context
- Es
- Kv
- Thought Garden — Fix Plan (simplified from audit)
- tg-core.js
- Thought-garden-main/app/services/document_service.py
- st
- FailedLoginLimiter
- st
- test_document_service.py
- test_garden_panel_xss.py
- UTCDateTime
- cn
- us
- ui
- sn
- Thought-garden-main/app/services/embedding_service.py
- conftest.py
- rb
- Streamlit port: shared design (Phase 6, 2026-10-12)
- test_streamlit_pages.py
- garden-component.js
- Y
- background_indexing_streamlit.py
- tg_ui/__init__.py
- CREDITS.md

## God Nodes (most connected - your core abstractions)
1. `Note` - 99 edges
2. `User` - 85 edges
3. `create_app()` - 60 edges
4. `Tag` - 60 edges
5. `Relationship` - 54 edges
6. `_fixture()` - 43 edges
7. `cs` - 38 edges
8. `cs` - 38 edges
9. `A()` - 35 edges
10. `A()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `create_app()` --indirect_call--> `note_view()`  [INFERRED]
  app/__init__.py → tg_ui/presenters.py
- `test_model_normalizes_email()` --calls--> `User`  [EXTRACTED]
  tests/test_auth.py → app/models.py
- `_Page` --uses--> `User`  [INFERRED]
  tests/test_browser_smoke.py → app/models.py
- `_ElementCollector` --uses--> `User`  [INFERRED]
  tests/test_markdown.py → app/models.py
- `TestCosineSimilarity` --uses--> `User`  [INFERRED]
  tests/test_services.py → app/models.py

## Import Cycles
- 3-file cycle: `app/services/document_service.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/document_service.py`
- 3-file cycle: `app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/search_service.py -> app/services/indexer.py`
- 4-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 4-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 4-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/tag_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 4-file cycle: `app/auth/__init__.py -> app/auth/routes.py -> app/services/onboarding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/auth/__init__.py`
- 4-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 4-file cycle: `app/garden/__init__.py -> app/garden/routes.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/garden/__init__.py`
- 4-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/search_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/search_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/search_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/indexer.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 5-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/indexer.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 5-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/similarity_service.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 5-file cycle: `app/auth/__init__.py -> app/auth/routes.py -> app/services/onboarding_service.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/auth/__init__.py`
- 5-file cycle: `app/auth/__init__.py -> app/auth/routes.py -> app/services/onboarding_service.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/auth/__init__.py`

## Communities (154 total, 29 thin omitted)

### Community 0 - "app/forms.py"
Cohesion: 0.08
Nodes (34): login(), logout(), profile(), login_required, route, Return `target` only if it is a path on this site, else None., register(), _safe_next_url() (+26 more)

### Community 1 - "app/models.py"
Cohesion: 0.07
Nodes (38): True when the database is at the latest Alembic revision., Create the local demo account with the starter garden., Re-embed every note and recompute relationships for every user., register_commands(), reindex(), schema_is_current(), seed_demo(), _configure_logging() (+30 more)

### Community 2 - "Thought-garden-main/tests/test_app.py"
Cohesion: 0.10
Nodes (7): clear_embedding_cache(), auth_client(), _set_embedding(), test_archiving_note_removes_dangling_garden_edges(), test_editing_note_does_not_destroy_other_notes_connections(), test_no_self_relationship(), _unit_vector()

### Community 3 - "Database Tables (5, all real SQLAlchemy models — see `app/models.py`)"
Cohesion: 0.07
Nodes (27): Application Code (`app/`), Authentication (`app/auth/routes.py`), Database Tables (5, all real SQLAlchemy models — see `app/models.py`), Demo Account, document_service.py, embedding_service.py, Garden (`app/garden/routes.py`), keyword_service.py (+19 more)

### Community 4 - "test_ux_a11y.py"
Cohesion: 0.10
Nodes (47): _all_pages(), app(), _app_fixture(), _authenticated_pages(), _csp(), csrf_app(), _csrf_from(), _csrf_login() (+39 more)

### Community 5 - "flowers.py"
Cohesion: 0.06
Nodes (69): test_categories_resolve_aliases_case_and_unknowns(), test_existing_categories_keep_their_values_and_colors(), test_generated_category_css_is_fresh(), test_generated_plants_are_fresh_and_complete(), test_retired_technical_categories_read_as_study_without_renaming(), build(), categories_css(), plant_files() (+61 more)

### Community 6 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 7 - "PEAS Description - Thought Garden Intelligent Agent"
Cohesion: 0.17
Nodes (8): Actuators, Agent Architecture, Environment, Future Enhancements, PEAS Description - Thought Garden Intelligent Agent, Performance Measure, Relationship Discovery Workflow, Sensors

### Community 8 - "compute_growth_stage"
Cohesion: 0.11
Nodes (36): compute_growth_score(), compute_growth_stage(), growth_icon_filename(), Combine a note's age and how connected it is into a 0.0-1.0 score. Neither…, Map a growth score onto one of GROWTH_STAGES., Look up the static SVG filename for a growth stage, defaulting to the seed icon…, test_a_week_old_well_connected_note_reaches_tree(), test_brand_new_isolated_note_is_a_seed() (+28 more)

### Community 9 - "garden-graph.js"
Cohesion: 0.07
Nodes (65): addGardenRipple(), allEdges, allNodes, applyGardenCategoryFilters(), applyGardenEmphasis(), bootGarden(), buildConnectionItem(), cameraAnimation() (+57 more)

### Community 10 - "Thought Garden Architecture"
Cohesion: 0.09
Nodes (21): 1. Application Factory Pattern, 2. Blueprint Organization, 3. Service Layer, 4. Embedding Storage, 5. Relationship Management, Data Flow, Database Schema, EmbeddingService (+13 more)

### Community 11 - "Thought Garden Roadmap"
Cohesion: 0.25
Nodes (8): AI Features, Contributing, Core Features, Enhancements, License, Thought Garden Roadmap, Version 1.0 (Current), Version 1.1 (Short-term)

### Community 12 - "Thought Garden Self Audit"
Cohesion: 0.09
Nodes (21): 10. Upload Health: 7/10, 11. UI/UX Health: 6/10, 12. Security Health: 7/10, 13. Maintainability Health: 6/10, 14. Documentation Health: 5/10, 1. Executive Summary, 2. Repository Health: 6/10, 3. Startup Health: 9/10 (+13 more)

### Community 13 - "🌱 Thought Garden"
Cohesion: 0.14
Nodes (14): Acknowledgments, AI Architecture, Architecture, Contributing, Core Features, Demo Workflow, Documentation, Hybrid Search (+6 more)

### Community 14 - "Thought Garden — Database Audit"
Cohesion: 0.17
Nodes (11): Cascade Behavior (verified against `app/models.py`, not assumed), Indexes (verified against `app/models.py`), note_embeddings table (`NoteEmbedding` model), note table, Open Recommendations (as of 2026-09-18), Relationship Quality Audit (historical — from a prior analysis run), relationship table, Schema Audit (verified against `app/models.py`) (+3 more)

### Community 15 - "Tables"
Cohesion: 0.13
Nodes (14): Database Schema - Thought Garden, Embedding Storage, Indexes, Migration Notes, Note, note_embeddings (Virtual Table), note_tags (Association), Overview (+6 more)

### Community 16 - "Thought Garden — Project History"
Cohesion: 0.15
Nodes (12): Architecture, Current State, Features Built, Fix 1: CSRFProtect Initialization, Fix 2: Similarity Threshold, Fix 3: Dark Mode + XSS, Known Limitations, Pre-Fix State (+4 more)

### Community 17 - "Route Definitions"
Cohesion: 0.15
Nodes (12): Authentication (`/auth`), Authentication Flow, Knowledge Garden (`/garden`), Main, Navigation Flow, Notes (`/notes`), Overview, Ownership Checks (+4 more)

### Community 18 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 19 - "Thought Garden Fix Plan"
Cohesion: 0.25
Nodes (7): FIX-001: CSRFProtect Initialization [P0 — COMPLETED], FIX-002: Lower Similarity Threshold [P1 — COMPLETED], FIX-003: Dark Mode + Template Variables [P2 — COMPLETED], FIX-004: XSS Vulnerability [P2 — COMPLETED], FIX-005: Dead Code + Imports [P3 — COMPLETED], Remaining Known Issues, Thought Garden Fix Plan

### Community 20 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 21 - "Thought Garden UML Flows"
Cohesion: 0.40
Nodes (4): Activity diagram: capture and connect knowledge, Restructure invariants, Sequence diagram: save or import a note, Thought Garden UML Flows

### Community 22 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 23 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 24 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 29 - "app/notes/routes.py"
Cohesion: 0.15
Nodes (30): archive(), archived(), create(), delete(), duplicates(), edit(), import_document(), list_notes() (+22 more)

### Community 30 - "app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js"
Cohesion: 0.05
Nodes (48): Ae(), be(), Ce(), D(), De(), di(), $e(), Ee() (+40 more)

### Community 31 - "tg_ui/static/vendor/vis-network/9.1.9/vis-network.min.js"
Cohesion: 0.05
Nodes (32): Av(), Ay(), Cb(), cM(), Cv(), Dp(), eb(), Ep() (+24 more)

### Community 32 - "2_Notes.py"
Cohesion: 0.18
Nodes (23): _cancel_confirm(), _do_archive(), _do_delete(), _filter_changed(), _note_form(), _pin_now(), Notes page — unified list / view / edit / create via session_state. Modes:…, render_create() (+15 more)

### Community 33 - "app/static/vendor/vis-network/9.1.9/vis-network.min.js"
Cohesion: 0.05
Nodes (29): Af(), Ay(), bp(), Cb(), cM(), Dp(), eb(), Ep() (+21 more)

### Community 34 - "NoteEmbedding"
Cohesion: 0.12
Nodes (11): NoteEmbedding, Stores each note's semantic embedding vector., cosine_similarity(), extract_keywords(), Pagination, app(), client(), TestCosineSimilarity (+3 more)

### Community 35 - "Tag"
Cohesion: 0.12
Nodes (24): Tag, category_badge_class(), category_color(), note_form_choices(), Flask-facing helpers over the shared category palette in tg_ui/categories.py…, Choices for NoteForm.category. Not exhaustive by design - the form field itself…, {background, border} for a category, for server-rendered garden data., get_or_create_tags() (+16 more)

### Community 37 - "remove"
Cohesion: 0.10
Nodes (3): on(), qn, remove()

### Community 38 - "tg_ui/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js"
Cohesion: 0.10
Nodes (22): be(), Ce(), D(), ei(), getDataAttributes(), Ie(), j(), k() (+14 more)

### Community 39 - "test_security.py"
Cohesion: 0.10
Nodes (38): app(), _assert_generic_failure(), _boom(), client(), _config_values(), _csrf_app(), _csrf_login(), _csrf_token() (+30 more)

### Community 40 - "remove"
Cohesion: 0.09
Nodes (4): on(), Q, qn, remove()

### Community 41 - "create_app"
Cohesion: 0.07
Nodes (38): create_app(), Ensure SECRET_KEY is set to a real value in production. In debug mode, the…, _set_sqlite_pragmas(), _validate_secret_key(), app(), auth_client(), client(), app() (+30 more)

### Community 42 - "A"
Cohesion: 0.16
Nodes (32): I(), A(), AN(), bN(), d(), dD(), dN(), DR() (+24 more)

### Community 43 - "A"
Cohesion: 0.16
Nodes (32): A(), AN(), bN(), dD(), dN(), DR(), EN(), fN() (+24 more)

### Community 44 - "streamlit_notes_ops.py"
Cohesion: 0.10
Nodes (22): queue_embedding_generation_streamlit(), Fire-and-forget: generate embedding + rescoring for note_id., create_note(), db_get_note(), delete_note(), get_note(), _get_or_create_tags(), list_filter_choices() (+14 more)

### Community 45 - "Database Tables (5, all real SQLAlchemy models — see `app/models.py`)"
Cohesion: 0.07
Nodes (27): Application Code (`app/`), Authentication (`app/auth/routes.py`), Database Tables (5, all real SQLAlchemy models — see `app/models.py`), Demo Account, document_service.py, embedding_service.py, Garden (`app/garden/routes.py`), keyword_service.py (+19 more)

### Community 46 - "Thought-garden-main/app/static/js/main.js"
Cohesion: 0.13
Nodes (19): allEdges, allNodes, clearGardenHighlight(), closePanel(), GARDEN_CATEGORY_BADGE_CLASS, GARDEN_CATEGORY_ORDER, gardenCategoryBadgeClass(), gardenLabelFont() (+11 more)

### Community 51 - "Bt"
Cohesion: 0.15
Nodes (3): Bt, getSelectorFromElement(), Y

### Community 52 - "streamlit_auth.py"
Cohesion: 0.16
Nodes (20): _build_navigation(), main(), Thought Garden — Streamlit entrypoint. Replaces run.py's Flask server. Run…, Shared sidebar shell: brand, session, garden counts, log out., _sidebar_nav(), _configured_password(), is_authenticated(), logout() (+12 more)

### Community 54 - "Thought Garden Architecture"
Cohesion: 0.09
Nodes (21): 1. Application Factory Pattern, 2. Blueprint Organization, 3. Service Layer, 4. Embedding Storage, 5. Relationship Management, Data Flow, Database Schema, EmbeddingService (+13 more)

### Community 55 - "Thought Garden Self Audit"
Cohesion: 0.09
Nodes (21): 10. Upload Health: 7/10, 11. UI/UX Health: 6/10, 12. Security Health: 7/10, 13. Maintainability Health: 6/10, 14. Documentation Health: 5/10, 1. Executive Summary, 2. Repository Health: 6/10, 3. Startup Health: 9/10 (+13 more)

### Community 56 - "app/main/routes.py"
Cohesion: 0.19
Nodes (15): dashboard(), export(), health(), index(), insights(), login_required, route, export_garden() (+7 more)

### Community 57 - "streamlit_ui.py"
Cohesion: 0.10
Nodes (25): presets(), (value, label, group) for every branded category, in display order., asset_data_uri(), environment(), macro(), Renders the shared macros outside Flask (the Streamlit port). Same templates,…, A static asset (path relative to static/) as a data: URI., Jinja environment over tg_ui/templates. With inline_assets, images become data:… (+17 more)

### Community 60 - "g"
Cohesion: 0.15
Nodes (20): I(), L(), AP(), BM(), cn(), d(), dM(), _e() (+12 more)

### Community 61 - "yd"
Cohesion: 0.14
Nodes (20): Av(), bd(), Bf(), ch(), dh(), dv(), ev(), _f() (+12 more)

### Community 62 - "Kv"
Cohesion: 0.18
Nodes (20): Cv(), Cy(), gy(), Hv(), Iv(), jv(), Kv(), nv() (+12 more)

### Community 63 - "Thought-garden-main/app/services/similarity_service.py"
Cohesion: 0.14
Nodes (19): cosine_similarity(), get_all_embeddings(), Every ready embedding for `user_id`'s notes, read straight from the database -…, Shared by similarity_service and search_service., A minimal stand-in for Flask-SQLAlchemy's Pagination object. Used wherever a…, SimplePagination, semantic_search(), hybrid_search() (+11 more)

### Community 65 - "app/services/__init__.py"
Cohesion: 0.20
Nodes (18): allowed_file(), build_plant_content(), chunk_text(), create_notes_from_document(), extract_text(), extract_text_from_md(), extract_text_from_pdf(), extract_text_from_txt() (+10 more)

### Community 66 - "ii"
Cohesion: 0.27
Nodes (22): Ae(), De(), di(), $e(), Ee(), fe(), ge(), ii() (+14 more)

### Community 67 - "Thought-garden-main/app/models.py"
Cohesion: 0.12
Nodes (7): Note, NoteEmbedding, UserMixin, Stores each note's semantic embedding vector. Previously created via raw SQL in…, Relationship, Tag, User

### Community 68 - "streamlit_garden_ops.py"
Cohesion: 0.11
Nodes (26): cache_data, cache_resource, build_html(), _connection_counts(), _edge_payload(), focus_payload(), garden_payload(), get_category_color() (+18 more)

### Community 69 - "Note"
Cohesion: 0.12
Nodes (23): Note, (other_note, Relationship) pairs, strongest first., _fts_match_expr(), _fts_search(), _fts_tokens(), hybrid_search(), keyword_search(), FTS5-backed keyword search: bm25() ranking, snippet() highlighting. Returns a… (+15 more)

### Community 70 - "g"
Cohesion: 0.12
Nodes (21): Af(), AP(), BM(), bp(), cn(), dM(), _e(), Ff() (+13 more)

### Community 71 - "User"
Cohesion: 0.18
Nodes (12): UserMixin, User, utcnow(), _seed(), test_indexer_process_pending_runs_synchronously_in_tests(), DocumentUploadForm, LoginForm, NoteForm (+4 more)

### Community 72 - "Tables"
Cohesion: 0.13
Nodes (14): Database Schema - Thought Garden, Embedding Storage, Indexes, Migration Notes, Note, note_embeddings (Virtual Table), note_tags (Association), Overview (+6 more)

### Community 73 - "🌱 Thought Garden"
Cohesion: 0.14
Nodes (14): Acknowledgments, AI Architecture, Architecture, Contributing, Core Features, Demo Workflow, Documentation, Hybrid Search (+6 more)

### Community 74 - "Relationship"
Cohesion: 0.10
Nodes (15): Relationship, _file_app(), test_foreign_keys_are_enforced(), test_sqlite_connections_get_pragmas(), _contrast(), garden_client(), _luminance(), _Note (+7 more)

### Community 75 - "test_auth.py"
Cohesion: 0.25
Nodes (19): _add_user(), _exhaust(), _login(), parametrize, _register(), test_database_rejects_case_duplicate_emails(), test_email_change_requires_correct_current_password(), test_email_change_with_correct_password_succeeds() (+11 more)

### Community 76 - "Thought Garden — Project History"
Cohesion: 0.15
Nodes (12): Architecture, Current State, Features Built, Fix 1: CSRFProtect Initialization, Fix 2: Similarity Threshold, Fix 3: Dark Mode + XSS, Known Limitations, Pre-Fix State (+4 more)

### Community 77 - "Route Definitions"
Cohesion: 0.15
Nodes (12): Authentication (`/auth`), Authentication Flow, Knowledge Garden (`/garden`), Main, Navigation Flow, Notes (`/notes`), Overview, Ownership Checks (+4 more)

### Community 78 - "Thought Garden — Database Audit"
Cohesion: 0.17
Nodes (11): Cascade Behavior (verified against `app/models.py`, not assumed), Indexes (verified against `app/models.py`), note_embeddings table (`NoteEmbedding` model), note table, Open Recommendations (as of 2026-09-18), Relationship Quality Audit (historical — from a prior analysis run), relationship table, Schema Audit (verified against `app/models.py`) (+3 more)

### Community 79 - "PEAS Description - Thought Garden Intelligent Agent"
Cohesion: 0.17
Nodes (8): Actuators, Agent Architecture, Environment, Future Enhancements, PEAS Description - Thought Garden Intelligent Agent, Performance Measure, Relationship Discovery Workflow, Sensors

### Community 81 - "tg_ui/static/js/main.js"
Cohesion: 0.15
Nodes (11): closeOpenPicker(), csrfToken(), enhanceSelect(), initPickers(), initTagInputs(), initTagSuggestions(), LIBRARY_SORTS, LIBRARY_STAGE_RANK (+3 more)

### Community 82 - "Non-Functional Requirements (NFR)"
Cohesion: 0.18
Nodes (11): 10. Recoverability, 1. Performance, 2. Availability, 3. Security, 4. Reliability, 5. Scalability, 6. Usability, 7. Accessibility (+3 more)

### Community 84 - "Non-Functional Requirements (NFR)"
Cohesion: 0.18
Nodes (11): 10. Recoverability, 1. Performance, 2. Availability, 3. Security, 4. Reliability, 5. Scalability, 6. Usability, 7. Accessibility (+3 more)

### Community 85 - "test_critical_bugs.py"
Cohesion: 0.19
Nodes (16): _add_note(), app(), client(), _no_semantic_results(), parametrize, test_dashboard_stats_exclude_archived_and_starter_notes(), test_edit_form_keeps_non_preset_category_selected(), test_edit_form_prefills_existing_tags() (+8 more)

### Community 86 - "CLAUDE.md — Thought Garden"
Cohesion: 0.18
Nodes (10): CLAUDE.md — Thought Garden, Current architecture / important behavior, Current known work / caveats, Documentation rules, Environment / startup, Git / branch safety, Important history / decisions, Key layout (+2 more)

### Community 87 - "CLAUDE.md — Thought Garden"
Cohesion: 0.22
Nodes (8): CLAUDE.md — Thought Garden, Docs are stale — don't trust them blindly, Environment setup — read this before `pip install`, Known bugs / rough edges (found by full-repo read, not yet fixed unless noted), Repo/branch state log, Repo layout, Verified working (2026-09-18), What this is

### Community 89 - "migrations/env.py"
Cohesion: 0.39
Nodes (7): get_engine(), get_engine_url(), get_metadata(), Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online()

### Community 90 - "Thought Garden Fix Plan"
Cohesion: 0.25
Nodes (7): FIX-001: CSRFProtect Initialization [P0 — COMPLETED], FIX-002: Lower Similarity Threshold [P1 — COMPLETED], FIX-003: Dark Mode + Template Variables [P2 — COMPLETED], FIX-004: XSS Vulnerability [P2 — COMPLETED], FIX-005: Dead Code + Imports [P3 — COMPLETED], Remaining Known Issues, Thought Garden Fix Plan

### Community 91 - "Thought Garden Roadmap"
Cohesion: 0.25
Nodes (8): AI Features, Contributing, Core Features, Enhancements, License, Thought Garden Roadmap, Version 1.0 (Current), Version 1.1 (Short-term)

### Community 92 - "Thought-garden-main/migrations/env.py"
Cohesion: 0.39
Nodes (7): get_engine(), get_engine_url(), get_metadata(), Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online()

### Community 93 - "Contributing to Thought Garden"
Cohesion: 0.29
Nodes (6): Before you start, Contributing to Thought Garden, Ground rules, Reporting issues, Running tests, Setup

### Community 94 - "Thought-garden-main/app/services/growth_service.py"
Cohesion: 0.33
Nodes (6): compute_growth_score(), compute_growth_stage(), growth_icon_filename(), Combine a note's age and how connected it is into a 0.0-1.0 score. Neither…, Map a growth score onto one of GROWTH_STAGES., Look up the static SVG filename for a growth stage, defaulting to the seed icon…

### Community 95 - "Contributing to Thought Garden"
Cohesion: 0.29
Nodes (6): Before you start, Contributing to Thought Garden, Ground rules, Reporting issues, Running tests, Setup

### Community 96 - "Extension Points"
Cohesion: 0.33
Nodes (6): DocumentProcessor, EmbeddingService, ExplanationService, Extension Points, SearchService, StorageService

### Community 97 - "rb"
Cohesion: 0.33
Nodes (6): aD(), gN(), kR(), rb(), sD(), wR()

### Community 98 - "Extension Points"
Cohesion: 0.33
Nodes (6): DocumentProcessor, EmbeddingService, ExplanationService, Extension Points, SearchService, StorageService

### Community 99 - "Installation"
Cohesion: 0.40
Nodes (5): Access, First Run, Installation, Prerequisites, Setup

### Community 101 - "Installation"
Cohesion: 0.40
Nodes (5): Access, First Run, Installation, Prerequisites, Setup

### Community 102 - "Version 2.0 (Medium-term)"
Cohesion: 0.50
Nodes (4): Advanced AI, Collaboration, Import/Export, Version 2.0 (Medium-term)

### Community 103 - "Version 3.0 (Long-term)"
Cohesion: 0.50
Nodes (4): Advanced Features, Infrastructure, Intelligence, Version 3.0 (Long-term)

### Community 105 - "Version 2.0 (Medium-term)"
Cohesion: 0.50
Nodes (4): Advanced AI, Collaboration, Import/Export, Version 2.0 (Medium-term)

### Community 106 - "Version 3.0 (Long-term)"
Cohesion: 0.50
Nodes (4): Advanced Features, Infrastructure, Intelligence, Version 3.0 (Long-term)

### Community 107 - "app/garden/routes.py"
Cohesion: 0.13
Nodes (29): data(), focus(), focus_data(), growth_icon_url(), index(), list_view(), note_detail(), _present_categories() (+21 more)

### Community 109 - "Thought-garden-main/config.py"
Cohesion: 0.40
Nodes (4): Config, _default_sqlite_uri(), SQLite location that is actually writable where the app runs. Streamlit…, Central configuration. Every env var the application reads is listed here with…

### Community 111 - "test_markdown.py"
Cohesion: 0.16
Nodes (21): _attribute_filter(), Note content -> safe HTML. Two independent layers: markdown-it runs with raw…, render_markdown(), sanitize_html(), _assert_inert(), _ElementCollector, _elements(), HTMLParser (+13 more)

### Community 112 - "Jn"
Cohesion: 0.08
Nodes (3): H, Jn, W

### Community 113 - "Thought-garden-main/app/notes/routes.py"
Cohesion: 0.25
Nodes (16): NoteForm, archive(), archived(), create(), delete(), edit(), get_or_create_tags(), import_document() (+8 more)

### Community 114 - "1_Dashboard.py"
Cohesion: 0.19
Nodes (13): _go_to_note(), quick_note_input(), Dashboard — quick note input + garden stats. The note maker here is a plain…, Compact note rows, each with its Open button alongside., _rows(), _focus(), _go_notes(), _handle() (+5 more)

### Community 115 - "test_browser_smoke.py"
Cohesion: 0.09
Nodes (38): _node_ring_pixel(), _Page, Browser smoke tests: the real app in Chromium, with CSRF and CSP enforced.…, Poll `expression` via page.evaluate. Playwright's wait_for_function evaluates…, RGBA of the canvas pixel on the top of a node's border ring, plus the node's…, A browser page that records console errors, page errors and CSP violations., test_category_picker_is_keyboard_operable_and_accepts_a_new_category(), test_clicking_a_focus_graph_node_keeps_its_colors() (+30 more)

### Community 116 - "yd"
Cohesion: 0.16
Nodes (18): bd(), Bf(), ch(), dh(), dv(), _f(), Hf(), hh() (+10 more)

### Community 117 - "app/services/embedding_service.py"
Cohesion: 0.17
Nodes (15): content_hash(), _decode_embedding_blob(), generate_embedding(), get_embedding(), get_embedding_text(), get_model(), get_ready_model(), _looks_like_pickle() (+7 more)

### Community 118 - "tests/test_app.py"
Cohesion: 0.10
Nodes (5): _set_embedding(), test_archiving_note_removes_dangling_garden_edges(), test_editing_note_does_not_destroy_other_notes_connections(), test_no_self_relationship(), _unit_vector()

### Community 120 - "test_migrations.py"
Cohesion: 0.32
Nodes (20): _close(), _file_app(), _insert_note_row(), _insert_tag_row(), _insert_user(), _insert_user_row(), _is_ignored_table(), _link_note_tag() (+12 more)

### Community 121 - "app_context"
Cohesion: 0.14
Nodes (20): dashboard_data(), insights_data(), _materialize(), Dashboard / Insights queries — Streamlit-side port of Flask main routes.…, Stats, lists and panels for the Dashboard page., Touch relations/attrs used later so lazy loads happen inside the context., Metrics for the Insights page ({} when the garden is empty)., current_user_id() (+12 more)

### Community 124 - "Kv"
Cohesion: 0.27
Nodes (15): Cy(), gy(), Hv(), jv(), Kv(), nv(), ov(), Qv() (+7 more)

### Community 125 - "Thought Garden — Fix Plan (simplified from audit)"
Cohesion: 0.15
Nodes (12): Before you start (one-time, ~30 min), Phase 0a — `fix/critical-bugs`, Phase 0b — `fix/security-and-cleanup`, Phase 1 — `refactor/foundations`, Phase 2 — `feature/indexer` (biggest payoff), Phase 3 — `feature/fts-search`, Phase 4 — `refactor/data-model`, Phase 5 — `feature/ux-a11y` (+4 more)

### Community 126 - "tg-core.js"
Cohesion: 0.18
Nodes (8): GARDEN_CATEGORIES, GARDEN_CATEGORY_BY_VALUE, gardenCategoryBadgeClass(), gardenCategorySlug(), hexToRgb(), hexToRgba(), plainText(), readingMinutes()

### Community 127 - "Thought-garden-main/app/services/document_service.py"
Cohesion: 0.23
Nodes (12): queue_embedding_generation(), Generate a note's embedding off the request thread. Previously the semantic…, Fire-and-forget: generate the given note's embedding, then recompute its…, allowed_file(), chunk_text(), create_notes_from_document(), extract_text(), extract_text_from_md() (+4 more)

### Community 129 - "FailedLoginLimiter"
Cohesion: 0.28
Nodes (3): FailedLoginLimiter, Seconds until `key` may try again, or 0 if not blocked., Sliding window of failed logins per key (client IP). State lives in this…

### Community 131 - "test_document_service.py"
Cohesion: 0.52
Nodes (6): _assert_valid_chunking(), _chunk_in_subprocess(), parametrize, test_chunk_text_randomized_inputs_terminate(), test_chunk_text_short_text_is_single_chunk(), test_chunk_text_terminates_and_covers_text()

### Community 132 - "test_garden_panel_xss.py"
Cohesion: 0.57
Nodes (6): _note(), Runs the garden note panel (tg_ui/static/js/garden-graph.js, shared by the…, _render_panel(), test_panel_connection_click_opens_that_note(), test_panel_renders_user_content_as_text_not_html(), test_panel_without_connections_shows_empty_message()

### Community 133 - "UTCDateTime"
Cohesion: 0.40
Nodes (3): Stores naive UTC (same on-disk format SQLite has always used here - no…, UTCDateTime, TypeDecorator

### Community 143 - "Thought-garden-main/app/services/embedding_service.py"
Cohesion: 0.31
Nodes (9): cosine_similarity(), _decode_embedding_blob(), generate_embedding(), get_all_embeddings(), get_embedding(), get_embedding_text(), get_model(), Shared by similarity_service and search_service - previously defined separately… (+1 more)

### Community 144 - "conftest.py"
Cohesion: 0.25
Nodes (5): FakeEmbeddingModel, _no_starter_garden_unless_marked(), Deterministic stand-in for SentenceTransformer: hashed bag of words, so texts…, _stub_ml_and_threads(), _sync_fts_schema_after_create_all()

### Community 145 - "rb"
Cohesion: 0.25
Nodes (8): aD(), gN(), kR(), mR(), rb(), sD(), wR(), yR()

### Community 146 - "Streamlit port: shared design (Phase 6, 2026-10-12)"
Cohesion: 0.25
Nodes (7): Data, Deploying, Files changed in this port, How it works, Streamlit port: shared design (Phase 6, 2026-10-12), What Streamlit still can't match, Why

### Community 147 - "test_streamlit_pages.py"
Cohesion: 0.32
Nodes (6): parametrize, Runs every Streamlit page headlessly (streamlit.testing AppTest) against a…, _run(), seeded(), test_notes_page_uses_shared_cards_and_escapes_titles(), test_page_renders_without_exceptions()

### Community 148 - "garden-component.js"
Cohesion: 0.80
Nodes (4): boot(), loadScript(), send(), setHeight()

### Community 150 - "background_indexing_streamlit.py"
Cohesion: 0.50
Nodes (3): Streamlit adapter for background embedding generation. Caller-facing API takes…, Load sentence-transformers once per process under st.cache_resource.…, warm_embedding_model()

## Knowledge Gaps
- **406 isolated node(s):** `gardenHost`, `allNodes`, `allEdges`, `gardenNodeAlpha`, `gardenEdgeAlpha` (+401 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Note` connect `Note` to `app/forms.py`, `app/models.py`, `Thought-garden-main/tests/test_app.py`, `test_ux_a11y.py`, `compute_growth_stage`, `Thought-garden-main/app/services/embedding_service.py`, `background_indexing_streamlit.py`, `app/notes/routes.py`, `NoteEmbedding`, `Tag`, `test_security.py`, `create_app`, `streamlit_notes_ops.py`, `app/main/routes.py`, `Thought-garden-main/app/services/similarity_service.py`, `app/services/__init__.py`, `streamlit_garden_ops.py`, `User`, `Relationship`, `test_critical_bugs.py`, `app/garden/routes.py`, `test_markdown.py`, `Thought-garden-main/app/notes/routes.py`, `test_browser_smoke.py`, `app/services/embedding_service.py`, `tests/test_app.py`, `app_context`, `Thought-garden-main/app/services/document_service.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `create_app()` connect `create_app` to `app/models.py`, `FailedLoginLimiter`, `Thought-garden-main/tests/test_app.py`, `test_ux_a11y.py`, `flowers.py`, `NoteEmbedding`, `Tag`, `test_security.py`, `Note`, `User`, `Relationship`, `test_auth.py`, `test_critical_bugs.py`, `app/garden/routes.py`, `test_markdown.py`, `test_browser_smoke.py`, `tests/test_app.py`, `test_migrations.py`, `app_context`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `User` connect `User` to `app/forms.py`, `app/models.py`, `NoteEmbedding`, `Tag`, `test_ux_a11y.py`, `Note`, `Thought-garden-main/tests/test_app.py`, `test_security.py`, `create_app`, `Relationship`, `test_auth.py`, `test_markdown.py`, `Thought-garden-main/app/notes/routes.py`, `test_browser_smoke.py`, `test_critical_bugs.py`, `tests/test_app.py`, `app_context`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Note` (e.g. with `RequestIDFilter` and `_Page`) actually correct?**
  _`Note` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `User` (e.g. with `LoginForm` and `NoteForm`) actually correct?**
  _`User` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `create_app()` (e.g. with `_set_sqlite_pragmas()` and `category_badge_class()`) actually correct?**
  _`create_app()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `Tag` (e.g. with `RequestIDFilter` and `_Page`) actually correct?**
  _`Tag` has 19 INFERRED edges - model-reasoned connections that need verification._