# Brain Architecture

## Overview

Brain is a local-first hybrid search engine designed for AI agents. It combines traditional keyword search with modern vector embeddings, all running locally without requiring API keys or cloud services.

## Core Components

### 1. Storage Layer (SQLite)

- **Pages Table**: Stores complete documents with metadata
- **Chunks Table**: Stores text segments with vector embeddings
- **Tags Table**: Categorization system
- **Links Table**: Entity relationships
- **Timeline Table**: Temporal events

### 2. Embedding Layer (Ollama)

- Model: `nomic-embed-text`
- Dimensions: 768
- Local inference via HTTP API
- No API key required

### 3. Search Layer (Hybrid)

#### Keyword Search
- SQLite LIKE pattern matching
- Token counting for relevance
- Fast for exact matches

#### Vector Search
- Cosine similarity calculation
- Full vector comparison in Python
- Better for semantic understanding

#### RRF Fusion
```python
score = Σ(1 / (k + rank_i))
```
- k = 60 (smoothing constant)
- Combines multiple ranked lists
- No training required

### 4. Deduplication (4 Layers)

1. **Source Deduplication**: Top 3 per page
2. **Similarity Deduplication**: Jaccard > 0.85
3. **Type Diversity**: Max 60% same type
4. **Page Cap**: Max 2 per page

## Data Flow

```
Input Query
    │
    ├──→ Keyword Search ──→ Ranked List ──┐
    │                                      ├──→ RRF ──→ Dedup ──→ Results
    └──→ Vector Search ───→ Ranked List ──┘
              ↑
              └── Ollama Embedding
```

## Page Lifecycle

1. **Import**: Parse markdown → Extract frontmatter → Chunk text
2. **Embed**: Generate vectors via Ollama
3. **Store**: Save to SQLite with relationships
4. **Query**: Hybrid search → RRF → Deduplication
5. **Update**: Incremental updates with hash checking

## Brain-Agent Loop

```
┌─────────────┐
│   Agent     │
│  Receives   │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Read      │
│  Context    │
│  (search)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Generate   │
│  Response   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Write     │
│  Learned    │
│   Facts     │
└─────────────┘
```

## Performance

- Query latency: < 100ms (keyword), < 500ms (hybrid)
- Embedding speed: ~50 chunks/sec (M1 Mac)
- Database: Handles 10K+ pages efficiently
- Memory: Minimal (lazy loading)

## Security

- All data stays local
- No network calls except to Ollama
- SQLite file can be encrypted
- No telemetry or analytics
