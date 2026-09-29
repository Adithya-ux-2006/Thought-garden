# Graph Report - thoughtgarden  (2026-09-24)

## Corpus Check
- 127 files · ~109,374 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2093 nodes · 4267 edges · 114 communities (86 shown, 28 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 191 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `276fcd93`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app/auth/routes.py
- app/services/__init__.py
- tests/test_app.py
- Database Tables (5, all real SQLAlchemy models — see `app/models.py`)
- User
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
- Note
- 2_Notes.py
- Thought-garden-main/app/static/vendor/vis-network/9.1.9/vis-network.min.js
- app/static/vendor/vis-network/9.1.9/vis-network.min.js
- app/models.py
- cs
- cs
- xt
- Jn
- update_relationships_for_note
- A
- A
- streamlit_notes_ops.py
- Database Tables (5, all real SQLAlchemy models — see `app/models.py`)
- Thought-garden-main/app/static/js/main.js
- xt
- remove
- remove
- qi
- qi
- Bt
- Thought-garden-main/tests/test_app.py
- W
- Thought Garden Architecture
- Thought Garden Self Audit
- app/main/routes.py
- g
- ao
- ao
- g
- yd
- Kv
- Ks
- Ks
- Bt
- yd
- Thought-garden-main/app/models.py
- Jn
- Es
- Kv
- Es
- Tables
- 🌱 Thought Garden
- Thought-garden-main/app/services/embedding_service.py
- st
- Thought Garden — Project History
- Route Definitions
- cn
- Thought Garden — Database Audit
- PEAS Description - Thought Garden Intelligent Agent
- semantic_pipeline_service.py
- cn
- qn
- Non-Functional Requirements (NFR)
- Non-Functional Requirements (NFR)
- Thought-garden-main/app/services/document_service.py
- CLAUDE.md — Thought Garden
- qn
- CLAUDE.md — Thought Garden
- migrations/env.py
- Thought Garden Fix Plan
- Thought Garden Roadmap
- Thought-garden-main/migrations/env.py
- Iv
- Contributing to Thought Garden
- Thought-garden-main/app/services/growth_service.py
- Contributing to Thought Garden
- rb
- Extension Points
- rb
- Extension Points
- Installation
- SimplePagination
- Installation
- Version 2.0 (Medium-term)
- Version 3.0 (Long-term)
- extract_keywords
- Version 2.0 (Medium-term)
- Version 3.0 (Long-term)
- Config

## God Nodes (most connected - your core abstractions)
1. `Note` - 74 edges
2. `User` - 55 edges
3. `Tag` - 51 edges
4. `Relationship` - 39 edges
5. `update_relationships_for_note()` - 38 edges
6. `cs` - 38 edges
7. `cs` - 38 edges
8. `A()` - 35 edges
9. `A()` - 35 edges
10. `Ib()` - 31 edges

## Surprising Connections (you probably didn't know these)
- `TestCosineSimilarity` --uses--> `User`  [INFERRED]
  tests/test_services.py → app/models.py
- `TestExtractKeywords` --uses--> `User`  [INFERRED]
  tests/test_services.py → app/models.py
- `TestGetRelationshipExplanation` --uses--> `User`  [INFERRED]
  tests/test_services.py → app/models.py
- `TestKeywordSearch` --uses--> `User`  [INFERRED]
  tests/test_services.py → app/models.py
- `TestLightweightSimilarity` --uses--> `User`  [INFERRED]
  tests/test_services.py → app/models.py

## Import Cycles
- 4-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/search_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 4-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/note_lifecycle_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`
- 5-file cycle: `app/search/__init__.py -> app/search/routes.py -> app/services/search_service.py -> app/services/embedding_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/search/__init__.py`
- 5-file cycle: `app/auth/__init__.py -> app/auth/routes.py -> app/services/onboarding_service.py -> app/services/note_lifecycle_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/auth/__init__.py`
- 5-file cycle: `app/notes/__init__.py -> app/notes/routes.py -> app/services/note_lifecycle_service.py -> app/services/semantic_pipeline_service.py -> thoughtgarden-src/Thought-garden-main/app/__init__.py -> app/notes/__init__.py`

## Communities (114 total, 28 thin omitted)

### Community 0 - "app/auth/routes.py"
Cohesion: 0.10
Nodes (30): login(), logout(), profile(), login_required, route, Return *target* only if it is a relative, same-origin path., register(), _safe_redirect_url() (+22 more)

### Community 1 - "app/services/__init__.py"
Cohesion: 0.13
Nodes (25): clear_embedding_cache(), cosine_similarity(), _decode_embedding_blob(), generate_embedding(), get_all_embeddings(), get_embedding(), get_embedding_text(), get_model() (+17 more)

### Community 2 - "tests/test_app.py"
Cohesion: 0.10
Nodes (9): app(), auth_client(), client(), fixture, _set_embedding(), test_archiving_note_removes_dangling_garden_edges(), test_editing_note_does_not_destroy_other_notes_connections(), test_no_self_relationship() (+1 more)

### Community 3 - "Database Tables (5, all real SQLAlchemy models — see `app/models.py`)"
Cohesion: 0.07
Nodes (27): Application Code (`app/`), Authentication (`app/auth/routes.py`), Database Tables (5, all real SQLAlchemy models — see `app/models.py`), Demo Account, document_service.py, embedding_service.py, Garden (`app/garden/routes.py`), keyword_service.py (+19 more)

### Community 4 - "User"
Cohesion: 0.12
Nodes (27): UserMixin, Tag, User, create_manual_note(), create_note_batch(), get_or_create_tags(), NoteLifecycleResult, parse_tag_names() (+19 more)

### Community 5 - "app/static/js/main.js"
Cohesion: 0.13
Nodes (19): allEdges, allNodes, clearGardenHighlight(), closePanel(), GARDEN_CATEGORY_BADGE_CLASS, GARDEN_CATEGORY_ORDER, gardenCategoryBadgeClass(), gardenLabelFont() (+11 more)

### Community 6 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 7 - "PEAS Description - Thought Garden Intelligent Agent"
Cohesion: 0.17
Nodes (8): Actuators, Agent Architecture, Environment, Future Enhancements, PEAS Description - Thought Garden Intelligent Agent, Performance Measure, Relationship Discovery Workflow, Sensors

### Community 8 - "compute_growth_stage"
Cohesion: 0.10
Nodes (38): data(), focus(), focus_data(), get_category_color(), growth_icon_url(), index(), note_detail(), login_required (+30 more)

### Community 9 - "app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js"
Cohesion: 0.06
Nodes (49): Ae(), be(), Ce(), D(), De(), di(), $e(), Ee() (+41 more)

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
Cohesion: 0.25
Nodes (16): NoteForm, archive(), archived(), create(), delete(), duplicates(), edit(), import_document() (+8 more)

### Community 30 - "Thought-garden-main/app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js"
Cohesion: 0.06
Nodes (46): Ae(), be(), Ce(), D(), De(), di(), $e(), Ee() (+38 more)

### Community 31 - "Note"
Cohesion: 0.07
Nodes (24): Note, NoteEmbedding, Stores each note's semantic embedding vector. Previously created via raw SQL in…, cosine_similarity(), extract_keywords(), Pagination, keyword_search(), get_relationship_explanation() (+16 more)

### Community 32 - "2_Notes.py"
Cohesion: 0.08
Nodes (47): _build_navigation(), main(), Thought Garden — Streamlit entrypoint. Replaces run.py's Flask server. Run…, Shared sidebar shell (replaces base.html navbar)., _sidebar_nav(), _configured_password(), current_user_id(), is_authenticated() (+39 more)

### Community 33 - "Thought-garden-main/app/static/vendor/vis-network/9.1.9/vis-network.min.js"
Cohesion: 0.05
Nodes (29): Af(), Ay(), bp(), Cb(), cM(), Dp(), eb(), Ep() (+21 more)

### Community 34 - "app/static/vendor/vis-network/9.1.9/vis-network.min.js"
Cohesion: 0.05
Nodes (27): Ay(), Cb(), cM(), Dp(), eb(), Ep(), ey(), fM() (+19 more)

### Community 35 - "app/models.py"
Cohesion: 0.09
Nodes (31): _configure_logging(), create_app(), Inject the current request's ID into every log record so it appears in the…, Set up a consistent log format with request ID and timestamp. Uses Flask's…, Ensure SECRET_KEY is set to a real value in production. In debug mode, the…, RequestIDFilter, _validate_secret_key(), Relationship (+23 more)

### Community 39 - "Jn"
Cohesion: 0.08
Nodes (3): H, Jn, W

### Community 40 - "update_relationships_for_note"
Cohesion: 0.16
Nodes (29): queue_embedding_generation(), Generate a note's embedding off the request thread. Previously the semantic…, Fire-and-forget: generate the given note's embedding, then recompute its…, allowed_file(), chunk_text(), create_notes_from_document(), extract_text(), extract_text_from_md() (+21 more)

### Community 41 - "A"
Cohesion: 0.16
Nodes (32): I(), A(), AN(), bN(), d(), dD(), dN(), DR() (+24 more)

### Community 42 - "A"
Cohesion: 0.16
Nodes (32): A(), AN(), bN(), dD(), dN(), DR(), EN(), fN() (+24 more)

### Community 43 - "streamlit_notes_ops.py"
Cohesion: 0.11
Nodes (24): invalidate_embedding_cache(), Drop a single note's cached embedding. Needed on delete: the note_embeddings…, queue_embedding_generation_streamlit(), Fire-and-forget: generate embedding + rescoring for note_id., app_context(), get_flask_app(), Create (and memoize) the Flask app used only as a DB/config host. Never call…, create_note() (+16 more)

### Community 44 - "Database Tables (5, all real SQLAlchemy models — see `app/models.py`)"
Cohesion: 0.07
Nodes (27): Application Code (`app/`), Authentication (`app/auth/routes.py`), Database Tables (5, all real SQLAlchemy models — see `app/models.py`), Demo Account, document_service.py, embedding_service.py, Garden (`app/garden/routes.py`), keyword_service.py (+19 more)

### Community 45 - "Thought-garden-main/app/static/js/main.js"
Cohesion: 0.13
Nodes (19): allEdges, allNodes, clearGardenHighlight(), closePanel(), GARDEN_CATEGORY_BADGE_CLASS, GARDEN_CATEGORY_ORDER, gardenCategoryBadgeClass(), gardenLabelFont() (+11 more)

### Community 51 - "Bt"
Cohesion: 0.15
Nodes (3): Bt, getSelectorFromElement(), Y

### Community 52 - "Thought-garden-main/tests/test_app.py"
Cohesion: 0.10
Nodes (9): app(), auth_client(), client(), fixture, _set_embedding(), test_archiving_note_removes_dangling_garden_edges(), test_editing_note_does_not_destroy_other_notes_connections(), test_no_self_relationship() (+1 more)

### Community 54 - "Thought Garden Architecture"
Cohesion: 0.09
Nodes (21): 1. Application Factory Pattern, 2. Blueprint Organization, 3. Service Layer, 4. Embedding Storage, 5. Relationship Management, Data Flow, Database Schema, EmbeddingService (+13 more)

### Community 55 - "Thought Garden Self Audit"
Cohesion: 0.09
Nodes (21): 10. Upload Health: 7/10, 11. UI/UX Health: 6/10, 12. Security Health: 7/10, 13. Maintainability Health: 6/10, 14. Documentation Health: 5/10, 1. Executive Summary, 2. Repository Health: 6/10, 3. Startup Health: 9/10 (+13 more)

### Community 56 - "app/main/routes.py"
Cohesion: 0.18
Nodes (16): dashboard(), export(), health(), index(), insights(), login_required, route, export_garden() (+8 more)

### Community 57 - "g"
Cohesion: 0.12
Nodes (21): Af(), AP(), BM(), bp(), cn(), dM(), _e(), Ff() (+13 more)

### Community 60 - "g"
Cohesion: 0.15
Nodes (20): I(), L(), AP(), BM(), cn(), d(), dM(), _e() (+12 more)

### Community 61 - "yd"
Cohesion: 0.14
Nodes (20): Av(), bd(), Bf(), ch(), dh(), dv(), ev(), _f() (+12 more)

### Community 62 - "Kv"
Cohesion: 0.18
Nodes (20): Cv(), Cy(), gy(), Hv(), Iv(), jv(), Kv(), nv() (+12 more)

### Community 66 - "yd"
Cohesion: 0.16
Nodes (18): bd(), Bf(), ch(), dh(), dv(), _f(), Hf(), hh() (+10 more)

### Community 67 - "Thought-garden-main/app/models.py"
Cohesion: 0.12
Nodes (7): Note, NoteEmbedding, UserMixin, Stores each note's semantic embedding vector. Previously created via raw SQL in…, Relationship, Tag, User

### Community 70 - "Kv"
Cohesion: 0.27
Nodes (15): Cy(), gy(), Hv(), jv(), Kv(), nv(), ov(), Qv() (+7 more)

### Community 72 - "Tables"
Cohesion: 0.13
Nodes (14): Database Schema - Thought Garden, Embedding Storage, Indexes, Migration Notes, Note, note_embeddings (Virtual Table), note_tags (Association), Overview (+6 more)

### Community 73 - "🌱 Thought Garden"
Cohesion: 0.14
Nodes (14): Acknowledgments, AI Architecture, Architecture, Contributing, Core Features, Demo Workflow, Documentation, Hybrid Search (+6 more)

### Community 74 - "Thought-garden-main/app/services/embedding_service.py"
Cohesion: 0.22
Nodes (11): cosine_similarity(), _decode_embedding_blob(), generate_embedding(), get_all_embeddings(), get_embedding(), get_embedding_text(), get_model(), invalidate_embedding_cache() (+3 more)

### Community 76 - "Thought Garden — Project History"
Cohesion: 0.15
Nodes (12): Architecture, Current State, Features Built, Fix 1: CSRFProtect Initialization, Fix 2: Similarity Threshold, Fix 3: Dark Mode + XSS, Known Limitations, Pre-Fix State (+4 more)

### Community 77 - "Route Definitions"
Cohesion: 0.15
Nodes (12): Authentication (`/auth`), Authentication Flow, Knowledge Garden (`/garden`), Main, Navigation Flow, Notes (`/notes`), Overview, Ownership Checks (+4 more)

### Community 79 - "Thought Garden — Database Audit"
Cohesion: 0.17
Nodes (11): Cascade Behavior (verified against `app/models.py`, not assumed), Indexes (verified against `app/models.py`), note_embeddings table (`NoteEmbedding` model), note table, Open Recommendations (as of 2026-09-18), Relationship Quality Audit (historical — from a prior analysis run), relationship table, Schema Audit (verified against `app/models.py`) (+3 more)

### Community 80 - "PEAS Description - Thought Garden Intelligent Agent"
Cohesion: 0.17
Nodes (8): Actuators, Agent Architecture, Environment, Future Enhancements, PEAS Description - Thought Garden Intelligent Agent, Performance Measure, Relationship Discovery Workflow, Sensors

### Community 81 - "semantic_pipeline_service.py"
Cohesion: 0.33
Nodes (9): SemanticJob, dispatch_job(), enrich_note_metadata(), infer_category(), process_job(), queue_semantic_pipeline(), Durable semantic enrichment pipeline for every created or updated note., Create durable jobs after persistence and immediately build fallback links. (+1 more)

### Community 84 - "Non-Functional Requirements (NFR)"
Cohesion: 0.18
Nodes (11): 10. Recoverability, 1. Performance, 2. Availability, 3. Security, 4. Reliability, 5. Scalability, 6. Usability, 7. Accessibility (+3 more)

### Community 85 - "Non-Functional Requirements (NFR)"
Cohesion: 0.18
Nodes (11): 10. Recoverability, 1. Performance, 2. Availability, 3. Security, 4. Reliability, 5. Scalability, 6. Usability, 7. Accessibility (+3 more)

### Community 86 - "Thought-garden-main/app/services/document_service.py"
Cohesion: 0.36
Nodes (9): allowed_file(), chunk_text(), create_notes_from_document(), extract_text(), extract_text_from_md(), extract_text_from_pdf(), extract_text_from_txt(), generate_title_from_content() (+1 more)

### Community 87 - "CLAUDE.md — Thought Garden"
Cohesion: 0.22
Nodes (8): CLAUDE.md — Thought Garden, Docs are stale — don't trust them blindly, Environment setup — read this before `pip install`, Known bugs / rough edges (found by full-repo read, not yet fixed unless noted), Repo/branch state log, Repo layout, Verified working (2026-09-18), What this is

### Community 89 - "CLAUDE.md — Thought Garden"
Cohesion: 0.22
Nodes (8): CLAUDE.md — Thought Garden, Docs are stale — don't trust them blindly, Environment setup — read this before `pip install`, Known bugs / rough edges (found by full-repo read, not yet fixed unless noted), Repo/branch state log, Repo layout, Verified working (2026-09-18), What this is

### Community 90 - "migrations/env.py"
Cohesion: 0.39
Nodes (7): get_engine(), get_engine_url(), get_metadata(), Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online()

### Community 91 - "Thought Garden Fix Plan"
Cohesion: 0.25
Nodes (7): FIX-001: CSRFProtect Initialization [P0 — COMPLETED], FIX-002: Lower Similarity Threshold [P1 — COMPLETED], FIX-003: Dark Mode + Template Variables [P2 — COMPLETED], FIX-004: XSS Vulnerability [P2 — COMPLETED], FIX-005: Dead Code + Imports [P3 — COMPLETED], Remaining Known Issues, Thought Garden Fix Plan

### Community 92 - "Thought Garden Roadmap"
Cohesion: 0.25
Nodes (8): AI Features, Contributing, Core Features, Enhancements, License, Thought Garden Roadmap, Version 1.0 (Current), Version 1.1 (Short-term)

### Community 93 - "Thought-garden-main/migrations/env.py"
Cohesion: 0.39
Nodes (7): get_engine(), get_engine_url(), get_metadata(), Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online()

### Community 94 - "Iv"
Cohesion: 0.29
Nodes (7): Av(), Cv(), ev(), Iv(), rv(), sv(), Uf()

### Community 95 - "Contributing to Thought Garden"
Cohesion: 0.29
Nodes (6): Before you start, Contributing to Thought Garden, Ground rules, Reporting issues, Running tests, Setup

### Community 96 - "Thought-garden-main/app/services/growth_service.py"
Cohesion: 0.33
Nodes (6): compute_growth_score(), compute_growth_stage(), growth_icon_filename(), Combine a note's age and how connected it is into a 0.0-1.0 score. Neither…, Map a growth score onto one of GROWTH_STAGES., Look up the static SVG filename for a growth stage, defaulting to the seed icon…

### Community 97 - "Contributing to Thought Garden"
Cohesion: 0.29
Nodes (6): Before you start, Contributing to Thought Garden, Ground rules, Reporting issues, Running tests, Setup

### Community 98 - "rb"
Cohesion: 0.33
Nodes (6): aD(), gN(), kR(), rb(), sD(), wR()

### Community 99 - "Extension Points"
Cohesion: 0.33
Nodes (6): DocumentProcessor, EmbeddingService, ExplanationService, Extension Points, SearchService, StorageService

### Community 100 - "rb"
Cohesion: 0.33
Nodes (6): aD(), gN(), kR(), rb(), sD(), wR()

### Community 101 - "Extension Points"
Cohesion: 0.33
Nodes (6): DocumentProcessor, EmbeddingService, ExplanationService, Extension Points, SearchService, StorageService

### Community 102 - "Installation"
Cohesion: 0.40
Nodes (5): Access, First Run, Installation, Prerequisites, Setup

### Community 104 - "Installation"
Cohesion: 0.40
Nodes (5): Access, First Run, Installation, Prerequisites, Setup

### Community 105 - "Version 2.0 (Medium-term)"
Cohesion: 0.50
Nodes (4): Advanced AI, Collaboration, Import/Export, Version 2.0 (Medium-term)

### Community 106 - "Version 3.0 (Long-term)"
Cohesion: 0.50
Nodes (4): Advanced Features, Infrastructure, Intelligence, Version 3.0 (Long-term)

### Community 107 - "extract_keywords"
Cohesion: 0.67
Nodes (3): extract_keywords(), suggest_tags(), get_relationship_explanation()

### Community 108 - "Version 2.0 (Medium-term)"
Cohesion: 0.50
Nodes (4): Advanced AI, Collaboration, Import/Export, Version 2.0 (Medium-term)

### Community 109 - "Version 3.0 (Long-term)"
Cohesion: 0.50
Nodes (4): Advanced Features, Infrastructure, Intelligence, Version 3.0 (Long-term)

## Knowledge Gaps
- **375 isolated node(s):** `allNodes`, `allEdges`, `GARDEN_CATEGORY_ORDER`, `GARDEN_CATEGORY_BADGE_CLASS`, `allNodes` (+370 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `I()` connect `A` to `app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js`, `yd`, `g`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `Note` connect `Note` to `app/auth/routes.py`, `app/services/__init__.py`, `tests/test_app.py`, `app/models.py`, `User`, `compute_growth_stage`, `update_relationships_for_note`, `Thought-garden-main/app/services/embedding_service.py`, `streamlit_notes_ops.py`, `semantic_pipeline_service.py`, `Thought-garden-main/tests/test_app.py`, `Thought-garden-main/app/services/document_service.py`, `app/main/routes.py`, `app/notes/routes.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `d()` connect `A` to `app/static/vendor/bootstrap/5.3.3/js/bootstrap.bundle.min.js`, `app/static/vendor/vis-network/9.1.9/vis-network.min.js`, `g`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Note` (e.g. with `RequestIDFilter` and `NoteLifecycleResult`) actually correct?**
  _`Note` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `User` (e.g. with `DocumentUploadForm` and `LoginForm`) actually correct?**
  _`User` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `Tag` (e.g. with `DocumentUploadForm` and `LoginForm`) actually correct?**
  _`Tag` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Relationship` (e.g. with `RequestIDFilter` and `TestCosineSimilarity`) actually correct?**
  _`Relationship` has 10 INFERRED edges - model-reasoned connections that need verification._