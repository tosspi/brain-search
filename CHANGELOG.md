# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-04-14

### Added
- Initial release
- Hybrid search (keyword + vector + RRF fusion)
- Ollama embedding support (nomic-embed-text)
- SQLite storage backend
- Brain-Agent Loop protocol
- 4-layer deduplication
- CLI interface
- Python API

### Features
- `brain init` - Initialize database
- `brain put` - Import markdown files
- `brain get` - Retrieve pages
- `brain search` - Keyword search
- `brain query` - Hybrid search
- `brain stats` - Statistics
- `brain list` - List pages
- `brain delete` - Remove pages

### Architecture
- Pages with compiled truth and timeline
- Chunking with overlap
- Tagging system
- Entity linking
- Timeline events

## Future Roadmap

### [1.1.0] - Planned
- Incremental embedding updates
- Import directory batch processing
- Export to JSON/CSV
- Web UI (optional)

### [1.2.0] - Planned
- Additional embedding models
- Custom chunking strategies
- Search result highlighting
- Query caching

### [2.0.0] - Planned
- Distributed search (optional)
- Plugin system
- Advanced analytics
