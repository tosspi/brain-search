#!/usr/bin/env python3
"""
Brain Core - Hybrid Search Engine with Ollama Embeddings

Architecture:
    - Ollama nomic-embed-text for local embeddings
    - SQLite for storage
    - Hybrid search: keyword + vector + RRF fusion
    - 4-layer deduplication

Based on gbrain by Garry Tan (MIT License)
Adapted to use local embeddings instead of OpenAI.
"""

import sqlite3
import json
import os
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple

# Default paths - can be overridden via environment
DEFAULT_DB_DIR = os.path.expanduser("~/.local/share/brain")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "brain.db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/embeddings")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nomic-embed-text:latest")

# Search constants
RRF_K = 60
COSINE_DEDUP_THRESHOLD = 0.85
MAX_TYPE_RATIO = 0.6
MAX_PER_PAGE = 2
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


class BrainEngine:
    """Core brain engine for knowledge management."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_db_dir()
        self.conn = None
    
    def _ensure_db_dir(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, mode=0o755)
    
    def get_db(self) -> sqlite3.Connection:
        """Get database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_db(self):
        """Initialize database schema."""
        db = self.get_db()
        
        # Pages table
        db.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL DEFAULT 'concept',
                title TEXT DEFAULT '',
                compiled_truth TEXT DEFAULT '',
                timeline TEXT DEFAULT '',
                frontmatter TEXT DEFAULT '{}',
                content_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Chunks table with embeddings
        db.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id INTEGER REFERENCES pages(id) ON DELETE CASCADE,
                slug TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_source TEXT DEFAULT 'compiled_truth',
                embedding BLOB,
                token_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tags table
        db.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id INTEGER REFERENCES pages(id) ON DELETE CASCADE,
                tag TEXT NOT NULL,
                UNIQUE(page_id, tag)
            )
        """)
        
        # Links table for entity relationships
        db.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_slug TEXT NOT NULL,
                to_slug TEXT NOT NULL,
                link_type TEXT DEFAULT '',
                context TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_slug, to_slug)
            )
        """)
        
        # Timeline events
        db.execute("""
            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id INTEGER REFERENCES pages(id) ON DELETE CASCADE,
                date TEXT NOT NULL,
                summary TEXT NOT NULL,
                detail TEXT DEFAULT '',
                source TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes for performance
        db.execute("CREATE INDEX IF NOT EXISTS idx_chunks_slug ON chunks(slug)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_tags_page ON tags(page_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_slug)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_slug)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_timeline_page ON timeline_events(page_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_pages_slug ON pages(slug)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_pages_type ON pages(type)")
        
        db.commit()
    
    def embed_text(self, text: str) -> List[float]:
        """Get embedding from Ollama."""
        import urllib.request
        
        truncated = text[:8000]
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": truncated
        }).encode("utf-8")
        
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["embedding"]
        except Exception as e:
            raise RuntimeError(f"Ollama embedding failed: {e}")
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into chunks."""
        if not text or not text.strip():
            return []
        
        words = text.split()
        if len(words) <= CHUNK_SIZE:
            return [{"text": text.strip(), "index": 0}]
        
        chunks = []
        for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk_words = words[i:i + CHUNK_SIZE]
            if chunk_words:
                chunks.append({
                    "text": " ".join(chunk_words),
                    "index": len(chunks)
                })
        return chunks
    
    def put_page(self, slug: str, content: str, 
                 page_type: str = "concept", 
                 title: str = "",
                 tags: List[str] = None,
                 no_embed: bool = False) -> Dict:
        """Insert or update a page."""
        db = self.get_db()
        tags = tags or []
        
        # Parse markdown content
        parts = content.split("\n---\n", 1)
        compiled_truth = parts[0] if parts else ""
        timeline = parts[1] if len(parts) > 1 else ""
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        title = title or slug.split("/")[-1].replace("-", " ").title()
        
        # Upsert page
        cursor = db.execute("""
            INSERT INTO pages (slug, type, title, compiled_truth, timeline, frontmatter, content_hash, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(slug) DO UPDATE SET
                type=excluded.type, title=excluded.title, compiled_truth=excluded.compiled_truth,
                timeline=excluded.timeline, frontmatter=excluded.frontmatter,
                content_hash=excluded.content_hash, updated_at=CURRENT_TIMESTAMP
        """, (slug, page_type, title, compiled_truth, timeline, json.dumps({}), content_hash))
        
        page_id = cursor.lastrowid or db.execute(
            "SELECT id FROM pages WHERE slug=?", (slug,)
        ).fetchone()[0]
        
        # Update tags
        db.execute("DELETE FROM tags WHERE page_id=?", (page_id,))
        for tag in tags:
            db.execute("INSERT OR IGNORE INTO tags (page_id, tag) VALUES (?, ?)", (page_id, tag))
        
        # Process timeline
        if timeline:
            for line in timeline.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                match = re.match(r"(\d{4}-\d{2}-\d{2})\s*\|\s*(.+)", line)
                if match:
                    date, summary = match.groups()
                    db.execute("""
                        INSERT OR IGNORE INTO timeline_events (page_id, date, summary, source)
                        VALUES (?, ?, ?, 'brain')
                    """, (page_id, date, summary))
        
        db.commit()
        
        # Generate chunks and embeddings
        chunks = self.chunk_text(compiled_truth)
        db.execute("DELETE FROM chunks WHERE slug=?", (slug,))
        
        if not no_embed and chunks:
            try:
                embeddings = [self.embed_text(c["text"]) for c in chunks]
                for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                    if emb:
                        import array
                        arr_bytes = array.array('d', emb).tobytes()
                        db.execute("""
                            INSERT INTO chunks (page_id, slug, chunk_index, chunk_text, chunk_source, embedding, token_count)
                            VALUES (?, ?, ?, ?, 'compiled_truth', ?, ?)
                        """, (page_id, slug, i, chunk["text"], sqlite3.Binary(arr_bytes), len(chunk["text"]) // 4))
            except Exception as e:
                print(f"[WARN] embedding failed for {slug}: {e}")
        
        db.commit()
        return {"slug": slug, "status": "imported", "chunks": len(chunks)}
    
    def get_page(self, slug: str) -> Optional[Dict]:
        """Get a page by slug."""
        db = self.get_db()
        row = db.execute("SELECT * FROM pages WHERE slug=?", (slug,)).fetchone()
        if not row:
            return None
        
        tags = [r[0] for r in db.execute(
            "SELECT tag FROM tags WHERE page_id=?", (row["id"],)
        ).fetchall()]
        
        return {
            "slug": row["slug"],
            "type": row["type"],
            "title": row["title"],
            "compiled_truth": row["compiled_truth"],
            "timeline": row["timeline"],
            "tags": tags,
            "updated_at": row["updated_at"],
        }
    
    def get_stats(self) -> Dict:
        """Get brain statistics."""
        db = self.get_db()
        pages = db.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        total_chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        embedded = db.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL").fetchone()[0]
        
        return {
            "pages": pages,
            "chunks": total_chunks,
            "embedded": embedded,
            "coverage": f"{(embedded/total_chunks*100):.1f}%" if total_chunks > 0 else "0%"
        }
