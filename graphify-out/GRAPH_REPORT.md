# Graph Report - thoughtgarden  (2026-09-29)

## Corpus Check
- 155 files · ~121,970 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2511 nodes · 5229 edges · 142 communities (107 shown, 35 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 209 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7135e250`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_auth.py
- app/services/embedding_service.py
- Note
- Database Tables (5, all real SQLAlchemy models — see `app/models.py`)
- test_ux_a11y.py
- app/static/js/main.js
- What You Must Do When Invoked
- PEAS Description - Thought Garden Intelligent Agent
- compute_growth_stage
- app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js
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
- Thought-garden-main/app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js
- app/static/vendor/vis-network/9.1.9/vis-network.min.js
- 2_Notes.py
- Thought-garden-main/app/static/vendor/vis-network/9.1.9/vis-network.min.js
- NoteEmbedding
- User
- cs
- cs
- xt
- test_security.py
- remove
- create_app
- A
- A
- app_context
- Database Tables (5, all real SQLAlchemy models — see `app/models.py`)
- Thought-garden-main/app/static/js/main.js
- xt
- remove
- qi
- qi
- Bt
- streamlit_auth.py
- Es
- Thought Garden Architecture
- Thought Garden Self Audit
- app/models.py
- g
- .hide
- ao
- g
- yd
- Kv
- Ks
- Ks
- Bt
- yd
- Thought-garden-main/app/models.py
- streamlit_garden_ops.py
- test_search_fts.py
- Kv
- Es
- Tables
- 🌱 Thought Garden
- Thought-garden-main/app/__init__.py
- st
- Thought Garden — Project History
- Route Definitions
- Thought Garden — Database Audit
- PEAS Description - Thought Garden Intelligent Agent
- cn
- qn
- Non-Functional Requirements (NFR)
- cn
- Non-Functional Requirements (NFR)
- test_critical_bugs.py
- CLAUDE.md — Thought Garden
- CLAUDE.md — Thought Garden
- rb
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
- app/__init__.py
- Thought-garden-main/config.py
- test_markdown.py
- Jn
- 4_Search.py
- 1_Dashboard.py
- test_browser_smoke.py
- ii
- Q
- tests/test_app.py
- W
- test_migrations.py
- ii
- Jn
- ui
- st
- Thought Garden — Fix Plan (simplified from audit)
- ui
- sn
- sn
- FailedLoginLimiter
- us
- test_document_service.py
- test_garden_panel_xss.py
- UTCDateTime
- Q
- Y

## God Nodes (most connected - your core abstractions)
1. `Note` - 92 edges
2. `User` - 80 edges
3. `Tag` - 56 edges
4. `create_app()` - 53 edges
5. `Relationship` - 49 edges
6. `cs` - 38 edges
7. `_fixture()` - 38 edges
8. `cs` - 38 edges
9. `A()` - 35 edges
10. `A()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `RequestIDFilter` --uses--> `Config`  [INFERRED]
  app/__init__.py → config.py
- `test_model_normalizes_email()` --calls--> `User`  [EXTRACTED]
  tests/test_auth.py → app/models.py
- `_Page` --uses--> `User`  [INFERRED]
  tests/test_browser_smoke.py → app/models.py
- `_ElementCollector` --uses--> `User`  [INFERRED]
  tests/test_markdown.py → app/models.py
- `TestCosineSimilarity` --uses--> `User`  [INFERRED]
  tests/test_services.py → app/models.py

## Import Cycles
- 3-file cycle: `app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/search_service.py -> app/services/indexer.py`
- 3-file cycle: `app/services/document_service.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/document_service.py`
- 4-file cycle: `app/garden/__init__.py -> app/garden/routes.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/garden/__init__.py`
- 4-file cycle: `app/auth/__init__.py -> app/auth/routes.py -> app/services/onboarding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/auth/__init__.py`
- 4-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 4-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/search_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 4-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 4-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 4-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/tag_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 5-file cycle: `app/garden/__init__.py -> app/garden/routes.py -> app/services/similarity_service.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/garden/__init__.py`
- 5-file cycle: `app/auth/__init__.py -> app/auth/routes.py -> app/services/onboarding_service.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/auth/__init__.py`
- 5-file cycle: `app/auth/__init__.py -> app/auth/routes.py -> app/services/onboarding_service.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/auth/__init__.py`
- 5-file cycle: `app/auth/__init__.py -> app/auth/routes.py -> app/services/onboarding_service.py -> app/services/tag_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/auth/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/indexer.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/indexer.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/search_service.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/search_service.py -> app/services/indexer.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/search_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> thoughtgarden-src/Thought-garden-main/app/services/__init__.py -> app/services/similarity_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`

## Communities (142 total, 35 thin omitted)

### Community 0 - "test_auth.py"
Cohesion: 0.08
Nodes (44): login(), logout(), profile(), login_required, route, Return `target` only if it is a path on this site, else None., register(), _safe_next_url() (+36 more)

### Community 1 - "app/services/embedding_service.py"
Cohesion: 0.07
Nodes (47): IndexJob, One row per note that needs (re-)embedding - acts as a small durable queue for…, content_hash(), cosine_similarity(), _decode_embedding_blob(), generate_embedding(), get_all_embeddings(), get_embedding() (+39 more)

### Community 2 - "Note"
Cohesion: 0.08
Nodes (15): Note, (other_note, Relationship) pairs, strongest first., lightweight_similarity(), Fast, deterministic similarity that needs no external ML model. Used by…, TestLightweightSimilarity, clear_embedding_cache(), prepare_starter_garden(), Copy the starter garden to a new user and connect it in one flow. (+7 more)

### Community 3 - "Database Tables (5, all real SQLAlchemy models — see `app/models.py`)"
Cohesion: 0.07
Nodes (27): Application Code (`app/`), Authentication (`app/auth/routes.py`), Database Tables (5, all real SQLAlchemy models — see `app/models.py`), Demo Account, document_service.py, embedding_service.py, Garden (`app/garden/routes.py`), keyword_service.py (+19 more)

### Community 4 - "test_ux_a11y.py"
Cohesion: 0.09
Nodes (49): Existing tag names worth adding to a note being written. Only ever suggests…, suggest_tags(), _all_pages(), app(), _app_fixture(), _authenticated_pages(), _csp(), csrf_app() (+41 more)

### Community 5 - "app/static/js/main.js"
Cohesion: 0.09
Nodes (23): allEdges, allNodes, buildConnectionItem(), clearGardenHighlight(), closePanel(), csrfToken(), GARDEN_CATEGORIES, GARDEN_CATEGORY_BADGE_CLASS (+15 more)

### Community 6 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 7 - "PEAS Description - Thought Garden Intelligent Agent"
Cohesion: 0.17
Nodes (8): Actuators, Agent Architecture, Environment, Future Enhancements, PEAS Description - Thought Garden Intelligent Agent, Performance Measure, Relationship Discovery Workflow, Sensors

### Community 8 - "compute_growth_stage"
Cohesion: 0.07
Nodes (55): data(), focus(), focus_data(), growth_icon_url(), index(), list_view(), note_detail(), login_required (+47 more)

### Community 9 - "app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js"
Cohesion: 0.11
Nodes (18): be(), D(), ei(), getDataAttributes(), Ie(), j(), k(), M() (+10 more)

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
Cohesion: 0.06
Nodes (71): NoteForm, dashboard(), export(), health(), index(), insights(), login_required, route (+63 more)

### Community 30 - "Thought-garden-main/app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js"
Cohesion: 0.10
Nodes (20): Ae(), be(), D(), ei(), getDataAttributes(), getSelectorFromElement(), Ie(), j() (+12 more)

### Community 31 - "app/static/vendor/vis-network/9.1.9/vis-network.min.js"
Cohesion: 0.05
Nodes (29): Af(), Ay(), bp(), Cb(), cM(), Dp(), eb(), Ep() (+21 more)

### Community 32 - "2_Notes.py"
Cohesion: 0.18
Nodes (23): _cancel_confirm(), _do_archive(), _do_delete(), _filter_changed(), _note_form(), _pin_now(), Notes page — unified list / view / edit / create via session_state. Modes:…, render_create() (+15 more)

### Community 33 - "Thought-garden-main/app/static/vendor/vis-network/9.1.9/vis-network.min.js"
Cohesion: 0.05
Nodes (29): Af(), Ay(), bp(), Cb(), cM(), Dp(), eb(), Ep() (+21 more)

### Community 34 - "NoteEmbedding"
Cohesion: 0.12
Nodes (10): NoteEmbedding, Stores each note's semantic embedding vector., cosine_similarity(), extract_keywords(), Pagination, client(), TestCosineSimilarity, TestExtractKeywords (+2 more)

### Community 35 - "User"
Cohesion: 0.12
Nodes (24): UserMixin, Tag, User, get_or_create_tags(), Case-insensitive per-user lookup-or-create. Tags are scoped per user (see Tag's…, test_no_self_relationship(), test_case_insensitive_duplicate_tag_within_one_user_is_rejected(), test_duplicate_exact_tag_name_within_one_user_is_rejected() (+16 more)

### Community 39 - "test_security.py"
Cohesion: 0.10
Nodes (38): app(), _assert_generic_failure(), _boom(), client(), _config_values(), _csrf_app(), _csrf_login(), _csrf_token() (+30 more)

### Community 40 - "remove"
Cohesion: 0.12
Nodes (3): on(), qn, remove()

### Community 41 - "create_app"
Cohesion: 0.09
Nodes (31): create_app(), FakeEmbeddingModel, _no_starter_garden_unless_marked(), Deterministic stand-in for SentenceTransformer: hashed bag of words, so texts…, _stub_ml_and_threads(), _sync_fts_schema_after_create_all(), app(), app() (+23 more)

### Community 42 - "A"
Cohesion: 0.16
Nodes (32): A(), AN(), bN(), dD(), dN(), DR(), EN(), fN() (+24 more)

### Community 43 - "A"
Cohesion: 0.16
Nodes (32): A(), AN(), bN(), dD(), dN(), DR(), EN(), fN() (+24 more)

### Community 44 - "app_context"
Cohesion: 0.13
Nodes (25): invalidate_embedding_cache(), Drop a single note's cached embedding. Needed on delete: the note_embeddings…, recalculate_all_relationships(), update_relationships_for_note(), queue_embedding_generation_streamlit(), Fire-and-forget: generate embedding + rescoring for note_id., app_context(), get_flask_app() (+17 more)

### Community 45 - "Database Tables (5, all real SQLAlchemy models — see `app/models.py`)"
Cohesion: 0.07
Nodes (27): Application Code (`app/`), Authentication (`app/auth/routes.py`), Database Tables (5, all real SQLAlchemy models — see `app/models.py`), Demo Account, document_service.py, embedding_service.py, Garden (`app/garden/routes.py`), keyword_service.py (+19 more)

### Community 46 - "Thought-garden-main/app/static/js/main.js"
Cohesion: 0.13
Nodes (19): allEdges, allNodes, clearGardenHighlight(), closePanel(), GARDEN_CATEGORY_BADGE_CLASS, GARDEN_CATEGORY_ORDER, gardenCategoryBadgeClass(), gardenLabelFont() (+11 more)

### Community 52 - "streamlit_auth.py"
Cohesion: 0.13
Nodes (26): ensure_all_relationships(), Backfill connections for every existing garden during application startup., _build_navigation(), main(), Thought Garden — Streamlit entrypoint. Replaces run.py's Flask server. Run…, Shared sidebar shell (replaces base.html navbar)., _sidebar_nav(), _configured_password() (+18 more)

### Community 54 - "Thought Garden Architecture"
Cohesion: 0.09
Nodes (21): 1. Application Factory Pattern, 2. Blueprint Organization, 3. Service Layer, 4. Embedding Storage, 5. Relationship Management, Data Flow, Database Schema, EmbeddingService (+13 more)

### Community 55 - "Thought Garden Self Audit"
Cohesion: 0.09
Nodes (21): 10. Upload Health: 7/10, 11. UI/UX Health: 6/10, 12. Security Health: 7/10, 13. Maintainability Health: 6/10, 14. Documentation Health: 5/10, 1. Executive Summary, 2. Repository Health: 6/10, 3. Startup Health: 9/10 (+13 more)

### Community 56 - "app/models.py"
Cohesion: 0.13
Nodes (11): Relationship, utcnow(), _seed(), _file_app(), test_foreign_keys_are_enforced(), test_sqlite_connections_get_pragmas(), dashboard(), index() (+3 more)

### Community 57 - "g"
Cohesion: 0.15
Nodes (20): I(), L(), AP(), BM(), cn(), d(), dM(), _e() (+12 more)

### Community 60 - "g"
Cohesion: 0.15
Nodes (20): I(), L(), AP(), BM(), cn(), d(), dM(), _e() (+12 more)

### Community 61 - "yd"
Cohesion: 0.14
Nodes (20): Av(), bd(), Bf(), ch(), dh(), dv(), ev(), _f() (+12 more)

### Community 62 - "Kv"
Cohesion: 0.18
Nodes (20): Cv(), Cy(), gy(), Hv(), Iv(), jv(), Kv(), nv() (+12 more)

### Community 65 - "Bt"
Cohesion: 0.14
Nodes (3): Bt, getSelectorFromElement(), Y

### Community 66 - "yd"
Cohesion: 0.14
Nodes (20): Av(), bd(), Bf(), ch(), dh(), dv(), ev(), _f() (+12 more)

### Community 67 - "Thought-garden-main/app/models.py"
Cohesion: 0.12
Nodes (7): Note, NoteEmbedding, UserMixin, Stores each note's semantic embedding vector. Previously created via raw SQL in…, Relationship, Tag, User

### Community 68 - "streamlit_garden_ops.py"
Cohesion: 0.13
Nodes (22): cache_data, cache_resource, build_html(), _connection_counts(), _edge_payload(), focus_payload(), garden_payload(), get_category_color() (+14 more)

### Community 69 - "test_search_fts.py"
Cohesion: 0.13
Nodes (22): SearchForm, login_required, route, search(), suggest(), hybrid_search(), keyword_search(), _fts_rowids() (+14 more)

### Community 70 - "Kv"
Cohesion: 0.18
Nodes (20): Cv(), Cy(), gy(), Hv(), Iv(), jv(), Kv(), nv() (+12 more)

### Community 72 - "Tables"
Cohesion: 0.13
Nodes (14): Database Schema - Thought Garden, Embedding Storage, Indexes, Migration Notes, Note, note_embeddings (Virtual Table), note_tags (Association), Overview (+6 more)

### Community 73 - "🌱 Thought Garden"
Cohesion: 0.14
Nodes (14): Acknowledgments, AI Architecture, Architecture, Contributing, Core Features, Demo Workflow, Documentation, Hybrid Search (+6 more)

### Community 74 - "Thought-garden-main/app/__init__.py"
Cohesion: 0.11
Nodes (22): Config, Central configuration. Every env var the application reads is listed here with…, isolated_config(), _migrate(), Point run.py's create_app() at a throwaway DB, never the real one., test_run_py_starts_without_seeding_or_backfill(), _configure_logging(), create_app() (+14 more)

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

### Community 82 - "Non-Functional Requirements (NFR)"
Cohesion: 0.18
Nodes (11): 10. Recoverability, 1. Performance, 2. Availability, 3. Security, 4. Reliability, 5. Scalability, 6. Usability, 7. Accessibility (+3 more)

### Community 84 - "Non-Functional Requirements (NFR)"
Cohesion: 0.18
Nodes (11): 10. Recoverability, 1. Performance, 2. Availability, 3. Security, 4. Reliability, 5. Scalability, 6. Usability, 7. Accessibility (+3 more)

### Community 85 - "test_critical_bugs.py"
Cohesion: 0.10
Nodes (26): get_model(), Load (once) and return the sentence-transformer model. Only the background…, A minimal stand-in for Flask-SQLAlchemy's Pagination object. Used wherever a…, SimplePagination, _add_note(), client(), _no_semantic_results(), parametrize (+18 more)

### Community 86 - "CLAUDE.md — Thought Garden"
Cohesion: 0.18
Nodes (10): CLAUDE.md — Thought Garden, Current architecture / important behavior, Current known work / caveats, Documentation rules, Environment / startup, Git / branch safety, Important history / decisions, Key layout (+2 more)

### Community 87 - "CLAUDE.md — Thought Garden"
Cohesion: 0.22
Nodes (8): CLAUDE.md — Thought Garden, Docs are stale — don't trust them blindly, Environment setup — read this before `pip install`, Known bugs / rough edges (found by full-repo read, not yet fixed unless noted), Repo/branch state log, Repo layout, Verified working (2026-09-18), What this is

### Community 88 - "rb"
Cohesion: 0.33
Nodes (6): aD(), gN(), kR(), rb(), sD(), wR()

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

### Community 107 - "app/__init__.py"
Cohesion: 0.09
Nodes (21): True when the database is at the latest Alembic revision., Create the local demo account with the starter garden., Re-embed every note and recompute relationships for every user., register_commands(), reindex(), schema_is_current(), seed_demo(), _configure_logging() (+13 more)

### Community 109 - "Thought-garden-main/config.py"
Cohesion: 0.40
Nodes (4): Config, _default_sqlite_uri(), SQLite location that is actually writable where the app runs. Streamlit…, Central configuration. Every env var the application reads is listed here with…

### Community 111 - "test_markdown.py"
Cohesion: 0.14
Nodes (23): _attribute_filter(), Note content -> safe HTML. Two independent layers: markdown-it runs with raw…, render_markdown(), sanitize_html(), app(), _assert_inert(), auth_client(), _ElementCollector (+15 more)

### Community 113 - "4_Search.py"
Cohesion: 0.19
Nodes (10): dashboard_data(), insights_data(), _materialize(), Dashboard / Insights queries — Streamlit-side port of Flask main routes.…, Stats, lists and panels for the Dashboard page., Touch relations/attrs used later so lazy loads happen inside the context., Metrics for the Insights page ({} when the garden is empty)., Search — hybrid (keyword + semantic) search with filters and paging. Port of… (+2 more)

### Community 114 - "1_Dashboard.py"
Cohesion: 0.27
Nodes (8): _go_to_note(), quick_note_input(), Dashboard — quick note input + garden stats. The note maker here is a plain…, _open(), Knowledge Garden — vis-network graph, full view or focus view. Port of Flask…, open_note(), Session-state keys and defaults for the Streamlit port., Jump to Notes view for a note (used by Garden side-list, etc.).

### Community 115 - "test_browser_smoke.py"
Cohesion: 0.14
Nodes (21): _node_ring_pixel(), _Page, Browser smoke tests: the real app in Chromium, with CSRF and CSP enforced.…, Poll `expression` via page.evaluate. Playwright's wait_for_function evaluates…, RGBA of the canvas pixel on the top of a node's border ring, plus the node's…, A browser page that records console errors, page errors and CSP violations., test_clicking_a_focus_graph_node_keeps_its_colors(), test_clicking_a_garden_node_keeps_its_colors_and_dims_unrelated_nodes() (+13 more)

### Community 116 - "ii"
Cohesion: 0.23
Nodes (25): Ae(), Ce(), De(), di(), $e(), Ee(), fe(), ge() (+17 more)

### Community 118 - "tests/test_app.py"
Cohesion: 0.10
Nodes (6): auth_client(), client(), _set_embedding(), test_archiving_note_removes_dangling_garden_edges(), test_editing_note_does_not_destroy_other_notes_connections(), _unit_vector()

### Community 120 - "test_migrations.py"
Cohesion: 0.32
Nodes (20): _close(), _file_app(), _insert_note_row(), _insert_tag_row(), _insert_user(), _insert_user_row(), _is_ignored_table(), _link_note_tag() (+12 more)

### Community 121 - "ii"
Cohesion: 0.29
Nodes (21): De(), di(), $e(), Ee(), fe(), ge(), ii(), je() (+13 more)

### Community 123 - "ui"
Cohesion: 0.20
Nodes (4): Ce(), mi(), pi(), ui()

### Community 125 - "Thought Garden — Fix Plan (simplified from audit)"
Cohesion: 0.15
Nodes (12): Before you start (one-time, ~30 min), Phase 0a — `fix/critical-bugs`, Phase 0b — `fix/security-and-cleanup`, Phase 1 — `refactor/foundations`, Phase 2 — `feature/indexer` (biggest payoff), Phase 3 — `feature/fts-search`, Phase 4 — `refactor/data-model`, Phase 5 — `feature/ux-a11y` (+4 more)

### Community 129 - "FailedLoginLimiter"
Cohesion: 0.28
Nodes (3): FailedLoginLimiter, Seconds until `key` may try again, or 0 if not blocked., Sliding window of failed logins per key (client IP). State lives in this…

### Community 131 - "test_document_service.py"
Cohesion: 0.52
Nodes (6): _assert_valid_chunking(), _chunk_in_subprocess(), parametrize, test_chunk_text_randomized_inputs_terminate(), test_chunk_text_short_text_is_single_chunk(), test_chunk_text_terminates_and_covers_text()

### Community 132 - "test_garden_panel_xss.py"
Cohesion: 0.57
Nodes (6): _note(), Runs main.js's garden note panel in Node against a minimal fake DOM and checks…, _render_panel(), test_panel_connection_click_opens_that_note(), test_panel_renders_user_content_as_text_not_html(), test_panel_without_connections_shows_empty_message()

### Community 133 - "UTCDateTime"
Cohesion: 0.40
Nodes (3): Stores naive UTC (same on-disk format SQLite has always used here - no…, UTCDateTime, TypeDecorator

## Knowledge Gaps
- **390 isolated node(s):** `allNodes`, `allEdges`, `GARDEN_CATEGORIES`, `GARDEN_CATEGORY_ORDER`, `GARDEN_CATEGORY_BADGE_CLASS` (+385 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Note` connect `Note` to `app/services/embedding_service.py`, `test_ux_a11y.py`, `compute_growth_stage`, `app/notes/routes.py`, `NoteEmbedding`, `User`, `test_security.py`, `create_app`, `app_context`, `app/models.py`, `streamlit_garden_ops.py`, `test_search_fts.py`, `Thought-garden-main/app/__init__.py`, `test_critical_bugs.py`, `app/__init__.py`, `test_markdown.py`, `4_Search.py`, `test_browser_smoke.py`, `tests/test_app.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `User` connect `User` to `test_auth.py`, `app/services/embedding_service.py`, `NoteEmbedding`, `Note`, `test_ux_a11y.py`, `test_search_fts.py`, `test_security.py`, `create_app`, `Thought-garden-main/app/__init__.py`, `app/__init__.py`, `app_context`, `test_markdown.py`, `test_browser_smoke.py`, `streamlit_auth.py`, `test_critical_bugs.py`, `tests/test_app.py`, `app/models.py`, `app/notes/routes.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `Tag` connect `User` to `app/services/embedding_service.py`, `NoteEmbedding`, `Note`, `test_ux_a11y.py`, `test_search_fts.py`, `create_app`, `Thought-garden-main/app/__init__.py`, `app/__init__.py`, `app_context`, `4_Search.py`, `test_browser_smoke.py`, `test_critical_bugs.py`, `tests/test_app.py`, `app/models.py`, `app/notes/routes.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Note` (e.g. with `RequestIDFilter` and `_Page`) actually correct?**
  _`Note` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `User` (e.g. with `LoginForm` and `NoteForm`) actually correct?**
  _`User` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `Tag` (e.g. with `RequestIDFilter` and `_Page`) actually correct?**
  _`Tag` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `create_app()` (e.g. with `_set_sqlite_pragmas()` and `category_badge_class()`) actually correct?**
  _`create_app()` has 4 INFERRED edges - model-reasoned connections that need verification._