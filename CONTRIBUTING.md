# Contributing to Thought Garden

## Before you start

Read `CLAUDE.md` in the repo root — it tracks the real, current state of the project (known bugs, what's actually fixed vs. still open, doc accuracy warnings) and is kept more up to date than any other single doc here. `docs/SELF_AUDIT.md` and `docs/FIX_PLAN.md` have the history of what's already been found and fixed.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # then set SECRET_KEY, or FLASK_DEBUG=1 for local development
flask db upgrade
flask seed-demo        # optional demo account
python run.py
```

First install is slow — `sentence-transformers` pulls in `torch`. See `CLAUDE.md` if you hit a build error on `numpy` on newer Python versions.

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

Check `CLAUDE.md` / `docs/SELF_AUDIT.md` before assuming the suite is green — as of the last audit, several tests failed due to a pytest fixture-scoping bug unrelated to application logic. Verify current status yourself rather than trusting an old test count in any doc, including this one.

## Ground rules

- **Don't trust the docs blindly.** Several docs in `docs/` (particularly older revisions of `docs/CURRENT_PROJECT_INVENTORY.md`) have drifted from the actual code in the past. When code and docs disagree, the code is right — fix the doc, don't assume the doc is describing intended-but-unimplemented behavior unless it says so explicitly.
- **Keep `CLAUDE.md` current.** If you fix something listed there as a known bug, or find a new one, update it in the same change. It's a log — add a dated entry, don't silently rewrite history.
- **Ownership checks matter.** Every note-scoped route filters by `user_id=current_user.id` — if you add a new route touching a `Note`, `Relationship`, or `NoteEmbedding`, make sure it does too.
- **Don't call `generate_embedding()` / load the SentenceTransformer model synchronously inside a request handler.** It's slow (model load + encode) and will make the request hang. Follow the existing pattern of using the lightweight scorer inline and deferring real embedding generation.
- **Security-sensitive changes** (anything touching `SECRET_KEY`, session handling, file upload validation, or how embeddings are serialized/deserialized) should be called out explicitly in your PR description — this app has had real issues in all of these areas before.

## Reporting issues

Note what you found and how you verified it (which file/line, what you actually observed running the code) rather than just a description — several existing docs were wrong because earlier findings weren't re-verified against the code before being written down.
