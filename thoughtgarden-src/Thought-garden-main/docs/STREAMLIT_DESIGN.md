# Streamlit port: shared design (Phase 6, 2026-10-12)

For review by the port's maintainer (Adithya). The deployed Streamlit app
now draws from the same design package as the Flask app, so redesigns no
longer have to be built twice. Nothing about auth, the database, embeddings,
`requirements.txt`, `.devcontainer` or Streamlit Cloud settings changed.

## Why

The Flask app and this port were separate UIs: the port rendered native
Streamlit widgets and never loaded any Flask template, CSS or JS, so the
Flask redesigns never reached the deployment. The only shared piece was
`.streamlit/config.toml`.

## How it works

`tg_ui/` at the repo root is the shared design package (it imports neither
Flask, Streamlit nor either app's models):

| Piece | What it is |
|---|---|
| `tg_ui/categories.py` | category palette: stored value, label, flower, colours |
| `tg_ui/flowers.py` + `build.py` | flower illustrations per category x growth stage, generated to `static/img/plants/` |
| `tg_ui/presenters.py` | note -> plain dict (title, excerpt, category, tags, reading time, stage, flower) |
| `tg_ui/templates/tg/notes.html` | shared Jinja macros: editorial card, compact row, journal page |
| `tg_ui/templates/tg/garden.html` | the Knowledge Garden markup |
| `tg_ui/static/` | CSS/JS/fonts/images (Flask's static folder; also the garden component's root) |

This port reaches it through one new module, `streamlit_ui.py`, which
appends the repo root to `sys.path` (appended, so the port's own `app` and
`config` still win) and provides:

- `apply_theme()` - injects the shared CSS with `st.html` (style-only, so it
  goes to the event container). It must run inside each page script:
  anything injected before `nav.run()` is replaced by the page run.
- `hero()`, `section()`, `note_card()`, `note_row()`, `journal()`,
  `flowerbeds()`, `connection_row()` - shared macros rendered to `st.html`.
- `garden()` - the Knowledge Garden as a bidirectional component
  (`components.declare_component(path=tg_ui/static)`). It runs the very same
  `garden-graph.js`/`garden.css` as the Flask page; Open/Edit/Focus clicks in
  its side panel come back to Python as the component value.

Styling only targets our own markup (`.tg-*`) and containers created with a
`key` (Streamlit's documented `st-key-<key>` class), never Streamlit's
generated class names.

## Files changed in this port

| File | Change |
|---|---|
| `streamlit_ui.py` | **new** - the adapter above |
| `app_streamlit.py` | applies the theme for the gate; `st.navigation(position="top")` with Material icons (also removes the sidebar's duplicate page list); sidebar keeps brand, session, garden counts, log out |
| `streamlit_pages/*.py` | each calls `ui.apply_theme()` after `require_auth()` |
| `streamlit_pages/1_Dashboard.py` | hero with stats, "Plant a thought" composer (category accepts a typed custom value, tags are a multiselect that accepts new ones), shared note rows, flowerbeds |
| `streamlit_pages/2_Notes.py` | shared editorial cards; note view as a journal card; related notes as "Connected thoughts"; form category/tags as above (a note's custom category stays selectable) |
| `streamlit_pages/3_Garden.py` | the shared garden component; whole/focus switch; list of plants as text alternative |
| `streamlit_pages/4_Search.py` | hero; results as shared note rows; flower-aware filter labels |
| `streamlit_garden_ops.py` | colours from the shared palette; payloads add `plant`, `notes` (panel data), `categories`, `user_id`. `build_html()`/`render_graph()` are now unused (left in place) |
| `streamlit_notes_ops.py` | category options from the shared palette; `note_views()` adds growth stage |
| `streamlit_widgets.py` | `note_card()` renders the shared card with Open/Pin underneath |
| `tests/test_streamlit_pages.py` | **new** - runs every page with `AppTest` (skipped without Streamlit) |

## Data

No schema change. Categories stay free text. Presets: Writing, Creativity,
Personal, Philosophy, Design, Research, Study, Business, AI, plus Other.
Software Engineering, Cybersecurity and Operating Systems are no longer
presets (one Study category instead; the subject goes in a tag). Notes that
already store them keep that text and take Study's colour and flower;
other unknown categories get the wildflower.

## What Streamlit still can't match

- Native widgets (selectbox, multiselect, inputs, buttons) take only theme
  styling: no custom menu animation, icons or grouping inside them.
- No dark-mode toggle (fixed theme from `config.toml`); the garden itself is
  always dark, as on Flask.
- `st.html` strips scripts: no parallax, falling leaves or animated list
  filtering outside the garden. CSS-only motion works but replays on every
  rerun, so it is kept to hero entrances.
- The garden lives in a fixed-height frame (760px on desktop).

## Deploying

`tg_ui/` must be present next to `thoughtgarden-src/` (Streamlit Cloud and
Codespaces clone the whole repo, so it is). If the port is ever split into
its own repository, copy `tg_ui/` in with it. After editing
`tg_ui/categories.py` or `tg_ui/flowers.py`, run `python -m tg_ui.build`.
