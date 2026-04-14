#!/usr/bin/env python3
"""
Hybrid Search Module

Implements:
- Keyword search (SQLite FTS-like)
- Vector search (cosine similarity)
- RRF fusion (Reciprocal Rank Fusion)
- 4-layer deduplication
"""

import sqlite3
import json
import array
from typing import List, Dict, Any, Optional
from .core import BrainEngine, RRF_K, COSINE_DEDUP_THRESHOLD, MAX_TYPE_RATIO, MAX_PER_PAGE


class HybridSearch:
    """Hybrid search combining keyword and vector search."""
    
    def __init__(self, engine: BrainEngine):
        self.engine = engine
    
    def search_keyword(self, query: str, limit: int = 20) -> List[Dict]:
        """Full-text keyword search."""
        db = self.engine.get_db()
        pattern = f"%{query}%"
        
        rows = db.execute("""
            SELECT c.slug, c.chunk_text, p.type, p.title,
                   COUNT(*) as match_count
            FROM chunks c JOIN pages p ON c.slug = p.slug
            WHERE c.chunk_text LIKE ?
            GROUP BY c.slug
            ORDER BY match_count DESC
            LIMIT ?
        """, (pattern, limit * 2)).fetchall()
        
        return [
            {
                "slug": r["slug"],
                "chunk_text": r["chunk_text"],
                "score": float(r["match_count"]),
                "type": r["type"],
                "title": r["title"],
            }
            for r in rows
        ]
    
    def search_vector(self, embedding: List[float], limit: int = 20) -> List[Dict]:
        """Vector similarity search."""
        db = self.engine.get_db()
        
        rows = db.execute("""
            SELECT c.slug, c.chunk_text, c.embedding, p.type, p.title
            FROM chunks c JOIN pages p ON c.slug = p.slug
            WHERE c.embedding IS NOT NULL
        """).fetchall()
        
        if not rows:
            return []
        
        results = []
        for row in rows:
            emb_bytes = row["embedding"]
            stored_emb = list(array.array('d', emb_bytes))
            similarity = self._cosine_similarity(embedding, stored_emb)
            
            results.append({
                "slug": row["slug"],
                "chunk_text": row["chunk_text"],
                "score": similarity,
                "type": row["type"],
                "title": row["title"],
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def query(self, query_text: str, limit: int = 20) -> List[Dict]:
        """Hybrid search with RRF fusion."""
        # Keyword search
        keyword_results = self.search_keyword(query_text, limit)
        
        # Vector search
        vector_results = []
        try:
            embedding = self.engine.embed_text(query_text)
            vector_results = self.search_vector(embedding, limit)
        except Exception as e:
            print(f"[WARN] Vector search failed: {e}")
        
        # RRF fusion
        fused = self._rrf_fusion([vector_results, keyword_results])
        return self._dedup_results(fused)[:limit]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    def _rrf_fusion(self, lists: List[List[Dict]]) -> List[Dict]:
        """Reciprocal Rank Fusion."""
        scores = {}
        
        for lst in lists:
            if not lst:
                continue
            for rank, r in enumerate(lst):
                key = f"{r['slug']}:{r['chunk_text'][:50]}"
                rrf_score = 1.0 / (RRF_K + rank)
                
                if key in scores:
                    scores[key]["score"] += rrf_score
                else:
                    scores[key] = {"result": r, "score": rrf_score}
        
        sorted_results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return [item["result"] for item in sorted_results]
    
    def _dedup_results(self, results: List[Dict]) -> List[Dict]:
        """4-layer deduplication."""
        if not results:
            return []
        
        # Layer 1: Top 3 per page
        by_page = {}
        for r in results:
            slug = r["slug"]
            if slug not in by_page:
                by_page[slug] = []
            by_page[slug].append(r)
        
        deduped = []
        for chunks in by_page.values():
            chunks.sort(key=lambda x: x["score"], reverse=True)
            deduped.extend(chunks[:3])
        deduped.sort(key=lambda x: x["score"], reverse=True)
        
        # Layer 2: Text similarity (Jaccard)
        kept = []
        for r in deduped:
            r_words = set(r["chunk_text"].lower().split())
            too_similar = False
            
            for k in kept:
                k_words = set(k["chunk_text"].lower().split())
                intersection = r_words & k_words
                union = r_words | k_words
                jaccard = len(intersection) / len(union) if union else 0
                
                if jaccard > COSINE_DEDUP_THRESHOLD:
                    too_similar = True
                    break
            
            if not too_similar:
                kept.append(r)
        deduped = kept
        
        # Layer 3: Type diversity
        max_per_type = max(1, int(len(deduped) * MAX_TYPE_RATIO))
        type_counts = {}
        type_kept = []
        
        for r in deduped:
            t = r.get("type", "concept")
            count = type_counts.get(t, 0)
            if count < max_per_type:
                type_kept.append(r)
                type_counts[t] = count + 1
        deduped = type_kept
        
        # Layer 4: Max per page
        page_counts = {}
        final = []
        
        for r in deduped:
            count = page_counts.get(r["slug"], 0)
            if count < MAX_PER_PAGE:
                final.append(r)
                page_counts[r["slug"]] = count + 1
        
        return final
