# Thought Garden Roadmap

## Version 1.0 (Current)

### Core Features
- ✅ User authentication (register, login, logout)
- ✅ Notes CRUD with categories and tags
- ✅ Semantic relationship discovery
- ✅ Knowledge Garden visualization
- ✅ Hybrid search (keyword + semantic)
- ✅ Document import (PDF, TXT, Markdown)
- ✅ Dashboard with insights
- ✅ Dark mode
- ✅ Responsive design

---

## Version 1.1 (Short-term)

### Enhancements
- [ ] Markdown editor with preview
- [ ] Note templates
- [ ] Bulk operations (select multiple notes)
- [ ] Export notes as Markdown/PDF
- [ ] Note versioning
- [ ] Relationship explanations with more detail
- [ ] Graph filtering improvements
- [ ] Keyboard shortcuts

### AI Features
- [ ] Automatic note summarization
- [ ] Smart category suggestions
- [ ] Duplicate note detection
- [ ] Relationship confidence scoring

---

## Version 2.0 (Medium-term)

### Advanced AI
- [ ] LLM integration for natural language queries
- [ ] RAG (Retrieval-Augmented Generation)
- [ ] AI chat with your knowledge base
- [ ] Automatic concept extraction
- [ ] Knowledge gap identification

### Import/Export
- [ ] Google Drive import
- [ ] Website/article import
- [ ] YouTube transcript import
- [ ] Obsidian vault import
- [ ] Notion import

### Collaboration
- [ ] Shared knowledge gardens
- [ ] Collaborative notes
- [ ] Comments and discussions
- [ ] Sharing permissions

---

## Version 3.0 (Long-term)

### Infrastructure
- [ ] PostgreSQL + pgvector support
- [ ] Cloud storage options
- [ ] API for third-party integrations
- [ ] Mobile apps (iOS/Android)
- [ ] PWA support

### Advanced Features
- [ ] Timeline view
- [ ] Spaced repetition flashcards
- [ ] Quiz generation
- [ ] Citation management
- [ ] Research paper analysis
- [ ] Audio note support
- [ ] Image understanding

### Intelligence
- [ ] Learning path recommendations
- [ ] Knowledge assessment
- [ ] Predictive connections
- [ ] Cross-user knowledge discovery
- [ ] Academic database integration

---

## Extension Points

### EmbeddingService
- **Current:** SentenceTransformer (local)
- **Future:** OpenAI embeddings, Cohere, or custom models

### SearchService
- **Current:** SQLite + local vectors
- **Future:** PostgreSQL + pgvector, Elasticsearch

### ExplanationService
- **Current:** Keyword overlap
- **Future:** LLM-generated explanations

### StorageService
- **Current:** Local filesystem
- **Future:** S3, Google Cloud Storage

### DocumentProcessor
- **Current:** PDF, TXT, Markdown
- **Future:** DOCX, HTML, images, audio

---

## Contributing

Interested in contributing? See our [Contributing Guidelines](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.