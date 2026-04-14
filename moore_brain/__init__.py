"""
Brain - Local hybrid search with Ollama embeddings

A lightweight, local-first knowledge brain for AI agents.
Based on the gbrain architecture (MIT License) by Garry Tan.

Features:
- Hybrid search: keyword + vector + RRF fusion
- Local embeddings via Ollama (free, no API key needed)
- SQLite storage (zero config)
- Brain-Agent Loop protocol support
"""

__version__ = "1.0.0"
__author__ = "Brain Contributors"
__license__ = "MIT"

from .core import BrainEngine
from .search import HybridSearch

__all__ = ["BrainEngine", "HybridSearch"]
