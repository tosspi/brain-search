#!/usr/bin/env python3
"""
Brain CLI - Command line interface
"""

import argparse
import json
import sys
from .core import BrainEngine
from .search import HybridSearch


def main():
    parser = argparse.ArgumentParser(
        description="Brain - Local hybrid search with Ollama embeddings"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # init
    init_parser = subparsers.add_parser("init", help="Initialize brain database")
    init_parser.add_argument("--db", help="Database path")
    
    # put
    put_parser = subparsers.add_parser("put", help="Add or update a page")
    put_parser.add_argument("slug", help="Page slug")
    put_parser.add_argument("file", help="Markdown file path")
    put_parser.add_argument("--type", default="concept", help="Page type")
    put_parser.add_argument("--title", help="Page title")
    put_parser.add_argument("--no-embed", action="store_true", help="Skip embedding")
    
    # get
    get_parser = subparsers.add_parser("get", help="Get a page")
    get_parser.add_argument("slug", help="Page slug")
    
    # search
    search_parser = subparsers.add_parser("search", help="Keyword search")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-n", type=int, default=20, help="Max results")
    
    # query (hybrid)
    query_parser = subparsers.add_parser("query", help="Hybrid search")
    query_parser.add_argument("question", help="Search question")
    query_parser.add_argument("-n", type=int, default=20, help="Max results")
    
    # stats
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    # list
    list_parser = subparsers.add_parser("list", help="List pages")
    list_parser.add_argument("--type", help="Filter by type")
    list_parser.add_argument("--tag", help="Filter by tag")
    list_parser.add_argument("-n", type=int, default=50, help="Max results")
    
    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a page")
    delete_parser.add_argument("slug", help="Page slug")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    db_path = getattr(args, 'db', None)
    engine = BrainEngine(db_path)
    
    if args.command == "init":
        engine.init_db()
        print(json.dumps({"status": "ok", "db": engine.db_path}))
    
    elif args.command == "put":
        with open(args.file, 'r') as f:
            content = f.read()
        result = engine.put_page(
            args.slug, content,
            page_type=args.type,
            title=args.title or "",
            no_embed=args.no_embed
        )
        print(json.dumps(result))
    
    elif args.command == "get":
        page = engine.get_page(args.slug)
        if page:
            print(json.dumps(page, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "not_found"}))
    
    elif args.command == "search":
        search = HybridSearch(engine)
        results = search.search_keyword(args.query, args.n)
        print(json.dumps(results, ensure_ascii=False))
    
    elif args.command == "query":
        search = HybridSearch(engine)
        results = search.query(args.question, args.n)
        print(json.dumps(results, ensure_ascii=False))
    
    elif args.command == "stats":
        stats = engine.get_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.command == "list":
        db = engine.get_db()
        query = "SELECT slug, type, title, updated_at FROM pages WHERE 1=1"
        params = []
        
        if args.type:
            query += " AND type=?"
            params.append(args.type)
        if args.tag:
            query += " AND id IN (SELECT page_id FROM tags WHERE tag=?)"
            params.append(args.tag)
        
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(args.n)
        
        rows = db.execute(query, params).fetchall()
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False))
    
    elif args.command == "delete":
        db = engine.get_db()
        db.execute("DELETE FROM pages WHERE slug=?", (args.slug,))
        db.commit()
        print(json.dumps({"status": "deleted", "slug": args.slug}))


if __name__ == "__main__":
    main()
