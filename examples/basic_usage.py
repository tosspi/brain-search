#!/usr/bin/env python3
"""Basic usage example for Brain."""

from brain_search import BrainEngine, HybridSearch

# Initialize
engine = BrainEngine()
engine.init_db()

# Add a page
content = """\
---
type: concept
title: Machine Learning
---

# Machine Learning

Machine learning is a subset of artificial intelligence that enables systems to learn from data.

## Types
- Supervised learning
- Unsupervised learning
- Reinforcement learning

---

2024-01-15 | Created this note
"""

result = engine.put_page(
    slug="concepts/ml",
    content=content,
    page_type="concept",
    title="Machine Learning",
    tags=["ai", "ml"]
)

print(f"Imported: {result}")

# Search
search = HybridSearch(engine)

# Keyword search
keyword_results = search.search_keyword("artificial intelligence", limit=5)
print("\nKeyword Results:")
for r in keyword_results:
    print(f"  {r['slug']}: {r['chunk_text'][:60]}...")

# Hybrid query
query_results = search.query("what is machine learning", limit=5)
print("\nHybrid Query Results:")
for r in query_results:
    print(f"  {r['slug']} (score: {r['score']:.3f}): {r['chunk_text'][:60]}...")

# Stats
stats = engine.get_stats()
print(f"\nStats: {stats}")
