# Graph Report - thoughtgarden  (2026-08-15)

## Corpus Check
- 54 files · ~33,125 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 465 nodes · 761 edges · 29 communities (25 shown, 4 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ef797c7b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- User
- services/__init__.py
- test_app.py
- Database Tables (6)
- Note
- main.js
- What You Must Do When Invoked
- Non-Functional Requirements (NFR)
- garden/routes.py
- Thought Garden Architecture
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
- notes/routes.py

## God Nodes (most connected - your core abstractions)
1. `Note` - 25 edges
2. `User` - 24 edges
3. `Tag` - 21 edges
4. `Thought Garden Self Audit` - 17 edges
5. `Relationship` - 14 edges
6. `create_note_batch()` - 13 edges
7. `🌱 Thought Garden` - 13 edges
8. `create_manual_note()` - 12 edges
9. `update_relationships_for_note()` - 12 edges
10. `What You Must Do When Invoked` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_no_self_relationship()` --calls--> `User`  [EXTRACTED]
  tests/test_app.py → app/models.py
- `test_lifecycle_persists_then_connects_and_imports()` --calls--> `User`  [EXTRACTED]
  tests/test_note_lifecycle.py → app/models.py
- `app()` --calls--> `User`  [EXTRACTED]
  tests/test_semantic_pipeline.py → app/models.py
- `app()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_app.py → app/__init__.py
- `app()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_note_lifecycle.py → app/__init__.py

## Import Cycles
- None detected.

## Communities (29 total, 4 thin omitted)

### Community 0 - "User"
Cohesion: 0.14
Nodes (22): login(), logout(), profile(), login_required, route, register(), DocumentUploadForm, LoginForm (+14 more)

### Community 1 - "services/__init__.py"
Cohesion: 0.11
Nodes (30): SemanticJob, clear_embedding_cache(), generate_embedding(), get_all_embeddings(), get_embedding(), get_embedding_text(), get_model(), extract_keywords() (+22 more)

### Community 2 - "test_app.py"
Cohesion: 0.09
Nodes (10): create_app(), app(), auth_client(), client(), fixture, app(), fixture, app() (+2 more)

### Community 3 - "Database Tables (6)"
Cohesion: 0.07
Nodes (29): Application Code (`app/`), Authentication, Configuration, Database Tables (6), Demo Account, DocumentService, EmbeddingService, Garden (+21 more)

### Community 4 - "Note"
Cohesion: 0.14
Nodes (25): Note, Relationship, allowed_file(), chunk_text(), extract_text(), extract_text_from_md(), extract_text_from_pdf(), extract_text_from_txt() (+17 more)

### Community 5 - "main.js"
Cohesion: 0.18
Nodes (16): allEdges, allNodes, closePanel(), escapeHtml(), initFocusGraph(), initGarden(), pixelNodeElements, pixelSprite() (+8 more)

### Community 6 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 7 - "Non-Functional Requirements (NFR)"
Cohesion: 0.04
Nodes (41): 10. Recoverability, 1. Performance, 2. Availability, 3. Security, 4. Reliability, 5. Scalability, 6. Usability, 7. Accessibility (+33 more)

### Community 8 - "garden/routes.py"
Cohesion: 0.47
Nodes (8): data(), focus(), get_category_color(), index(), note_detail(), pipeline_status(), login_required, route

### Community 10 - "Thought Garden Architecture"
Cohesion: 0.09
Nodes (21): 1. Application Factory Pattern, 2. Blueprint Organization, 3. Service Layer, 4. Embedding Storage, 5. Relationship Management, Data Flow, Database Schema, EmbeddingService (+13 more)

### Community 12 - "Thought Garden Self Audit"
Cohesion: 0.09
Nodes (21): 10. Upload Health: 7/10, 11. UI/UX Health: 6/10, 12. Security Health: 7/10, 13. Maintainability Health: 6/10, 14. Documentation Health: 5/10, 1. Executive Summary, 2. Repository Health: 6/10, 3. Startup Health: 9/10 (+13 more)

### Community 13 - "🌱 Thought Garden"
Cohesion: 0.11
Nodes (19): Access, Acknowledgments, AI Architecture, Architecture, Contributing, Core Features, Demo Workflow, Documentation (+11 more)

### Community 14 - "Thought Garden — Database Audit"
Cohesion: 0.12
Nodes (15): Cascade Behavior, Current State, Data Integrity Audit, Indexes, note_embeddings Table, notes Table, Ownership Consistency, Recommendations (+7 more)

### Community 15 - "Tables"
Cohesion: 0.13
Nodes (14): Database Schema - Thought Garden, Embedding Storage, Indexes, Migration Notes, Note, note_embeddings (Virtual Table), note_tags (Association), Overview (+6 more)

### Community 16 - "Thought Garden — Project History"
Cohesion: 0.15
Nodes (12): Architecture, Current State, Features Built, Fix 1: CSRFProtect Initialization, Fix 2: Similarity Threshold, Fix 3: Dark Mode + XSS, Known Limitations, Pre-Fix State (+4 more)

### Community 17 - "Route Definitions"
Cohesion: 0.15
Nodes (12): Authentication (`/auth`), Authentication Flow, Dashboard (`/`), Knowledge Garden (`/garden`), Navigation Flow, Notes (`/notes`), Overview, Ownership Checks (+4 more)

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

### Community 29 - "notes/routes.py"
Cohesion: 0.17
Nodes (26): dashboard(), export(), health(), index(), insights(), login_required, route, archive() (+18 more)

## Knowledge Gaps
- **203 isolated node(s):** `allNodes`, `allEdges`, `pixelNodeElements`, `Usage`, `What graphify is for` (+198 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Note` connect `Note` to `User`, `services/__init__.py`, `test_app.py`, `garden/routes.py`, `notes/routes.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `Tag` connect `User` to `services/__init__.py`, `test_app.py`, `Note`, `notes/routes.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `User` connect `User` to `services/__init__.py`, `test_app.py`, `Note`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `User` (e.g. with `DocumentUploadForm` and `LoginForm`) actually correct?**
  _`User` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Tag` (e.g. with `DocumentUploadForm` and `LoginForm`) actually correct?**
  _`Tag` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `allNodes`, `allEdges`, `pixelNodeElements` to the rest of the system?**
  _203 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `User` be split into smaller, more focused modules?**
  _Cohesion score 0.13978494623655913 - nodes in this community are weakly interconnected._