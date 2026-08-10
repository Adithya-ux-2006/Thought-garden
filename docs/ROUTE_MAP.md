# Thought Garden — Route Map

## Overview
12 unique routes across 5 blueprints. All routes require authentication except `/` and `/auth/login` and `/auth/register`.

## Route Definitions

### Public Routes
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET | `/` | landing.html | No | Marketing landing page |

### Authentication (`/auth`)
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET/POST | `/auth/login` | auth/login.html | No | User login |
| GET/POST | `/auth/register` | auth/register.html | No | New user registration |
| GET | `/auth/logout` | redirect | No | User logout |
| GET/POST | `/auth/profile` | auth/profile.html | **Yes** | User profile |

### Notes (`/notes`)
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET | `/notes/` | notes/index.html | **Yes** | List all notes |
| GET/POST | `/notes/create` | notes/create.html | **Yes** | Create note |
| GET | `/notes/<id>` | notes/view.html | **Yes** | View note + connections |
| GET/POST | `/notes/<id>/edit` | notes/edit.html | **Yes** | Edit note (owner only) |
| POST | `/notes/<id>/delete` | redirect to /notes/ | **Yes** | Delete note (owner only) |
| POST | `/notes/<id>/pin` | redirect to /notes/<id> | **Yes** | Toggle pin (owner only) |
| POST | `/notes/<id>/archive` | redirect to /notes/<id> | **Yes** | Toggle archive (owner only) |
| POST | `/notes/import` | redirect to /notes/ | **Yes** | Import document |

### Knowledge Garden (`/garden`)
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET | `/garden/` | garden/index.html | **Yes** | Interactive graph |
| GET | `/garden/data` | JSON API | **Yes** | Graph nodes + edges |
| GET | `/garden/note/<id>` | JSON API | **Yes** | Note detail for graph |
| GET | `/garden/focus/<id>` | garden/index.html | **Yes** | Focus mode |

### Search (`/search`)
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET | `/search/` | search/index.html | **Yes** | Search results |

### Dashboard (`/`)
| Method | URL | Template | Login Required | Description |
|--------|-----|----------|----------------|-------------|
| GET | `/dashboard` | dashboard.html | **Yes** | User dashboard |
| GET | `/insights` | insights.html | **Yes** | Learning insights |

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
1. User visits `/auth/register` or `/auth/login`
2. On success, `login_user(user)` creates session
3. `@login_required` decorator on protected routes redirects to `/auth/login?next=...`
4. On logout, session cleared, redirect to `/`

## Ownership Checks
- Note edit: `note.user_id != current_user.id` → 403
- Note delete: `note.user_id != current_user.id` → 403
- Note pin: `note.user_id != current_user.id` → 403
- Note archive: `note.user_id != current_user.id` → 403
- Profile: `current_user` only
