# 🌱 Thought Garden

**Your ideas shouldn't live in isolation.**

Thought Garden is an AI-powered personal knowledge management application that understands your notes, discovers hidden connections, and turns scattered knowledge into an explorable garden.

---

## The Problem

Traditional notes apps are just digital filing cabinets. Your ideas sit in isolation, disconnected from related thoughts. Important relationships between concepts are lost, and valuable knowledge becomes buried and forgotten.

## The Solution

Thought Garden uses AI to understand the meaning of your content and automatically discover relationships between different pieces of knowledge. It transforms your notes into a living knowledge graph where connections emerge naturally.

**CAPTURE** → **UNDERSTAND** → **CONNECT** → **DISCOVER**

---

## Core Features

- **Intelligent Notes:** Create, organize, and tag your knowledge
- **AI-Powered Connections:** Automatic semantic relationship discovery
- **Knowledge Garden:** Interactive visual graph of your ideas
- **Hybrid Search:** Find notes by meaning, not just keywords
- **Document Import:** Analyze PDFs, Markdown, and text files
- **Smart Insights:** Discover patterns in your knowledge
- **Privacy-First:** Your data stays on your device

---

## Architecture

```
thought-garden/
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── forms.py             # WTForms
│   ├── auth/                # Authentication blueprint
│   ├── notes/               # Notes CRUD blueprint
│   ├── garden/              # Knowledge graph blueprint
│   ├── search/              # Hybrid search blueprint
│   ├── main/                # Dashboard blueprint
│   └── services/            # Business logic
│       ├── embedding_service.py
│       ├── similarity_service.py
│       ├── keyword_service.py
│       ├── search_service.py
│       └── document_service.py
├── instance/                # Database files
├── tests/                   # Test suite
└── docs/                    # Documentation
```

---

## AI Architecture

### Semantic Relationship Discovery

1. **Immediate Connection Discovery:** Titles, content, tags, and categories are compared without blocking the web request
2. **Stored Semantic Embeddings:** Existing SentenceTransformer vectors enhance similarity when available
3. **Backfill on demand:** `flask reindex` recomputes connections for every note
4. **Top-N Selection:** The strongest connections are retained for each note
5. **Explanation:** Overlapping keywords identify why notes are connected

### Hybrid Search

- **Keyword Search:** SQL substring matching (`ILIKE`) for exact matches — not SQLite FTS5; that's on the roadmap, not yet implemented
- **Semantic Search:** Vector similarity for conceptual matches
- **Combined Ranking:** Results merged via Reciprocal Rank Fusion and ranked by relevance

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, Flask |
| Database | SQLite (SQLAlchemy ORM) |
| AI/ML | sentence-transformers, NumPy |
| Frontend | HTML5, Jinja2, Bootstrap 5, Vanilla JS |
| Graph | vis-network |
| PDF | PyPDF2 |

---

## Installation

### Prerequisites

- Python 3.9+
- pip
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/thought-garden.git
cd thought-garden

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file, then either set SECRET_KEY
# (python -c "import secrets; print(secrets.token_hex(32))")
# or, for local development only, set FLASK_DEBUG=1
cp .env.example .env

# Create or upgrade the database schema
flask db upgrade

# Optional: local demo account with the starter garden
flask seed-demo

# Run application
python run.py
```

> **Note:** on some branches of this repo, `.env` is not yet actually
> loaded by the app (no `load_dotenv()` call), so editing it has no
> effect until that's wired up — check whether `app/__init__.py` calls
> `load_dotenv()` before relying on `.env` overrides taking effect. If
> it doesn't, export the variables at the OS/shell level instead.

### First Run

`python run.py` never creates tables or data; it refuses to start until `flask db upgrade` has brought the schema up to date. New users receive the starter notes (from `app/data/starter_notes.json`) and their connections during registration, then enter the completed visual Garden. Run `flask reindex` to recompute every connection.

**Existing database:** back up `instance/thought_garden.db`, then run `flask db upgrade`. A database created before migrations existed (no `alembic_version` table) needs `flask db stamp a1b2c3d4e5f6` first.

### Access

Open http://127.0.0.1:5000 in your browser.

**Demo Account** (only after `flask seed-demo`; local use only):
- Email: demo@thoughtgarden.app
- Password: demo1234

---

## Demo Workflow

1. **Create an account**
2. **Wait briefly** while the starter notes and connections are prepared in one flow
3. **Enter the Knowledge Garden** and explore the visible network
4. **Create or import a note** and let its connections build automatically
5. **Click any node** to inspect its related notes in the side panel

---

## Documentation

- [Non-Functional Requirements](docs/NFR.md)
- [PEAS Description](docs/PEAS.md)
- [Roadmap](docs/ROADMAP.md)

---

## Contributing

Contributions welcome! Please read our contributing guidelines first.

---

## License

MIT License

---

## Acknowledgments

- [Sentence Transformers](https://www.sbert.net/)
- [vis-network](https://visjs.github.io/vis-network/)
- [Bootstrap](https://getbootstrap.com/)
- [Flask](https://flask.palletsprojects.com/)
