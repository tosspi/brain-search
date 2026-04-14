# Brain - Local Hybrid Search

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/ollama-nomic--embed--text-green.svg)](https://ollama.com)

A lightweight, local-first knowledge brain for AI agents.

基于 gbrain 架构的本地混合搜索引擎，完全免费，无需 API Key。

---

## English

### Features

- **Hybrid Search**: Keyword + Vector + RRF fusion
- **Local Embeddings**: Ollama `nomic-embed-text` (free, no API key)
- **SQLite Storage**: Zero configuration, single file
- **Brain-Agent Loop**: Read before responding, write after learning
- **4-Layer Deduplication**: Source, similarity, type, page cap

### Quick Start

```bash
# 1. Install Ollama and pull model
ollama pull nomic-embed-text

# 2. Install Brain
pip install brain-search

# 3. Initialize
brain init

# 4. Import notes
brain put my-note notes.md --type concept

# 5. Search
brain query "your question"
```

### Commands

| Command | Description |
|---------|-------------|
| `brain init` | Initialize database |
| `brain put <slug> <file>` | Import markdown |
| `brain get <slug>` | Retrieve page |
| `brain search <query>` | Keyword search |
| `brain query <question>` | Hybrid search |
| `brain stats` | Statistics |
| `brain list` | List pages |

### Architecture

```
Keyword Search (SQLite) ──┐
                          ├── RRF Fusion ── 4-Layer Dedup ── Results
Vector Search (Ollama) ───┘
```

---

## 中文

### 特性

- **混合搜索**：关键词 + 向量 + RRF 融合
- **本地嵌入**：Ollama `nomic-embed-text`，完全免费
- **SQLite 存储**：零配置，单文件数据库
- **Brain-Agent 循环**：先读取再回答，学习后写入
- **四层去重**：来源、相似度、类型多样性、页面上限

### 快速开始

```bash
# 1. 安装 Ollama 并拉取模型
ollama pull nomic-embed-text

# 2. 安装 Brain
pip install brain-search

# 3. 初始化数据库
brain init

# 4. 导入笔记
brain put my-note notes.md --type concept

# 5. 搜索
brain query "你的问题"
```

### 命令列表

| 命令 | 说明 |
|------|------|
| `brain init` | 初始化数据库 |
| `brain put <slug> <file>` | 导入 Markdown 文件 |
| `brain get <slug>` | 获取页面 |
| `brain search <query>` | 关键词搜索 |
| `brain query <question>` | 混合搜索 |
| `brain stats` | 统计信息 |
| `brain list` | 列出所有页面 |

### 架构说明

```
关键词搜索 (SQLite) ──┐
                      ├── RRF 融合 ── 四层去重 ── 结果
向量搜索 (Ollama) ────┘
```

### RRF 融合算法

```python
# Reciprocal Rank Fusion
score = Σ(1 / (k + rank_i))
# k = 60 (平滑常数)
```

### 四层去重

1. **来源去重**：每页最多保留 top 3 chunks
2. **相似度去重**：Jaccard 相似度 > 0.85 去重
3. **类型多样性**：同类型不超过总数 60%
4. **页面上限**：每页最多 2 个结果

---

## Comparison / 对比

| Tool | Embeddings | Database | Cost | Local |
|------|-----------|----------|------|-------|
| **Brain** | Ollama | SQLite | Free | ✅ |
| gbrain | OpenAI | PGLite/Postgres | $ | ❌ |
| Mem0 | OpenAI | Cloud | $$$ | ❌ |

---

## Page Format / 页面格式

```markdown
---
type: concept
title: My Note
tags: [tag1, tag2]
---

# Compiled Truth
Main content here.

---

2024-01-15 | Timeline event description
```

---

## Configuration / 配置

Environment variables:

- `BRAIN_DB_PATH`: Database path (`~/.local/share/brain/brain.db`)
- `OLLAMA_URL`: Ollama API URL (`http://localhost:11434`)
- `OLLAMA_MODEL`: Model name (`nomic-embed-text`)

---

## Acknowledgments / 致谢

Based on [gbrain](https://github.com/garrytan/gbrain) by Garry Tan (MIT License).

Adapted to use Ollama embeddings instead of OpenAI.

---

## License

MIT License - see [LICENSE](LICENSE) file.
