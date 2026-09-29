# PEAS Description - Thought Garden Intelligent Agent

## Performance Measure

The intelligent recommendation agent in Thought Garden is evaluated on:

- **Relevance:** Connections between notes should be semantically meaningful
- **Accuracy:** Similarity scores should reflect true conceptual relationships
- **Coverage:** The system should discover connections across different knowledge areas
- **Timeliness:** Recommendations generated quickly during note creation
- **Explanations:** Connection explanations should be clear and helpful
- **User Satisfaction:** Users should find discovered connections useful

---

## Environment

The agent operates within:

- **User Knowledge Base:** Collection of notes created by the user
- **Notes:** Text content with titles, categories, and tags
- **Documents:** Imported PDFs, Markdown files, and text files
- **Tags:** User-defined labels for organizing notes
- **Categories:** High-level topic classifications
- **Existing Relationships:** Previously discovered connections between notes
- **Embeddings:** Vector representations of note content

---

## Actuators

The agent produces:

- **Related Note Suggestions:** Recommendations for similar notes when viewing a note
- **Knowledge Graph Edges:** Visual connections between notes in the garden
- **Semantic Search Results:** Ranked results based on meaning, not just keywords
- **Suggested Tags:** Automatic tag recommendations for new notes
- **Extracted Keywords:** Important terms identified from note content
- **Connection Explanations:** Human-readable explanations of why notes are connected
- **Insights:** Statistics and patterns about the user's knowledge

---

## Sensors

The agent perceives:

- **Note Titles:** Headlines or names of knowledge entries
- **Note Content:** Full text body of notes
- **Uploaded Document Text:** Extracted text from PDFs, Markdown, and text files
- **Tags:** User-assigned labels
- **Categories:** Topic classifications
- **Existing Knowledge Structure:** Current relationships and embeddings
- **User Interactions:** Which notes are viewed, edited, or pinned

---

## Agent Architecture

The intelligent agent uses a **hybrid architecture** combining:

1. **Sentence Embeddings (Primary)**
   - Model: all-MiniLM-L6-v2 (sentence-transformers)
   - Generates 384-dimensional vectors representing note meaning
   - Enables semantic comparison beyond keyword matching

2. **Cosine Similarity**
   - Compares embedding vectors to find related notes
   - Threshold: configurable (default 0.7)
   - Maximum connections per note: configurable (default 5)

3. **Keyword Extraction (Supporting)**
   - TF-IDF-based keyword identification
   - Used for connection explanations
   - Lightweight alternative to full NLP

4. **TF-IDF (Fallback)**
   - Baseline for keyword search
   - Comparison with semantic results

---

## Relationship Discovery Workflow

```
User creates/updates note
        ↓
Combine: title + content + tags + category
        ↓
Generate sentence embedding (384-dim vector)
        ↓
Compare against all user's note embeddings
        ↓
Calculate cosine similarity scores
        ↓
Filter by threshold (≥ 0.7)
        ↓
Keep top N connections (≤ 5)
        ↓
Create/update Relationship records
        ↓
Generate explanation (overlapping keywords)
        ↓
Display in Knowledge Garden
```

---

## Future Enhancements

- **LLM Explanations:** Replace keyword explanations with natural language
- **RAG:** Retrieval-augmented generation for answering questions
- **Citation Detection:** Identify references between notes
- **Concept Extraction:** Auto-generate concept maps
- **Adaptive Thresholds:** Adjust similarity based on user feedback