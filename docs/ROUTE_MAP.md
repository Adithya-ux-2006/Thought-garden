# Thought Garden — Route Map

> Rewritten 2026-09-18 against `app.url_map` directly (21 registered
> routes, verified by iterating it in code — not counted by hand).
> The previous version undercounted routes, referenced template files
> that don't exist (`notes/index.html`, `search/index.html` — the real
> files are `notes/list.html`, `search/search.html`), and described
> ownership checks as 403s when they're actually 404s. See below.

## Overview
21 routes across 5 blueprints. All routes require authentication except `/`, `/auth/login`, and `/auth/register`.

## Route Definitions

### Public Routes
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET | `/` | main/landing.html | No | Marketing landing page (redirects to `/dashboard` if already logged in) |

### Authentication (`/auth`)
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET/POST | `/auth/login` | auth/login.html | No | User login |
| GET/POST | `/auth/register` | auth/register.html | No | New user registration; seeds a starter garden on first registration |
| POST | `/auth/logout` | redirect to `/` | Yes | User logout (CSRF-protected form) |
| GET/POST | `/auth/profile` | auth/profile.html | Yes | User profile + password change |

### Notes (`/notes`)
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET | `/notes/` | notes/list.html | Yes | List notes (filterable by archived/pinned/category/tag) |
| GET/POST | `/notes/create` | notes/create.html | Yes | Create note (also hosts the document-import form) |
| GET | `/notes/<id>` | notes/view.html | Yes | View note + related notes |
| GET/POST | `/notes/<id>/edit` | notes/edit.html | Yes | Edit note (owner only — see Ownership Checks) |
| POST | `/notes/<id>/delete` | redirect to `/notes/` | Yes | Delete note (owner only) |
| POST | `/notes/<id>/pin` | redirect to `/notes/<id>` | Yes | Toggle pin (owner only) |
| POST | `/notes/<id>/archive` | redirect to `/notes/<id>` | Yes | Toggle archive (owner only) |
| POST | `/notes/import` | redirect to `/notes/<id>` or `/notes/` | Yes | Import PDF/TXT/MD document, may create multiple notes (one per chunk) |
| GET | `/notes/archived` | redirect to `/notes/?archived=1` | Yes | Convenience redirect into the archived filter |

### Knowledge Garden (`/garden`)
| Method | URL | Returns | Login Required | Description |
|--------|-----|---------|----------------|-------------|
| GET | `/garden/` | garden/index.html | Yes | Interactive graph page |
| GET | `/garden/data` | JSON | Yes | Full graph: nodes + edges for the current user |
| GET | `/garden/note/<id>` | JSON | Yes | Note detail + connections, for the graph's side panel |
| GET | `/garden/focus/<id>` | JSON | Yes | Depth-limited subgraph centered on one note |

### Search (`/search`)
| Method | URL | Returns | Login Required | Description |
|--------|-----|---------|----------------|-------------|
| GET/POST | `/search/` | search/search.html | Yes | Hybrid (keyword + semantic) search results |
| GET | `/search/api/suggest` | JSON | Yes | Autocomplete suggestions (title match, min 2 chars) |

### Main
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET | `/dashboard` | main/dashboard.html | Yes | Stats, recent notes, most-connected notes, orphans |
| GET | `/insights` | main/insights.html | Yes | Aggregate insights (top category, strongest connection, etc.) |

## Navigation Flow
```
Landing → Register/Login → Dashboard
Dashboard → Notes List → Create/View/Edit/Delete
Dashboard → Knowledge Garden → Focus Mode
Dashboard → Search → Results
Dashboard → Insights
Notes View → Related Notes sidebar
```

## Authentication Flow
1. User visits `/auth/register` or `/auth/login`.
2. On success, `login_user(user)` creates the session; registration also runs `prepare_starter_garden()` for a first-time user.
3. The `@login_required` decorator on protected routes redirects to `/auth/login?next=...`.
4. On logout, session is cleared and the user is redirected to `/`.

## Ownership Checks

**Correction from a prior version of this doc:** these are **404s, not 403s.** Every owner-scoped note route queries with the ownership filter built in:

```python
note = Note.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
```

If the note exists but belongs to someone else, the `user_id` filter means the query simply finds nothing, and `first_or_404()` returns a 404 — not a 403. This is a deliberate (if perhaps incidental) security property: a 403 would confirm to an attacker that a note with that ID exists but isn't theirs; a 404 doesn't leak that. Routes with this check: `notes.view`, `notes.edit`, `notes.delete`, `notes.pin`, `notes.archive`, and the `garden` blueprint's note-scoped routes (`note_detail`, `focus`). `auth.profile` doesn't need an ownership check — it always operates on `current_user`.
