import sys
import os
import argparse
from sqlalchemy.orm import Session

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.session import SessionLocal
from services.search import search_events
from services.memory import search_similar_memories

def compare_search(query: str):
    db = SessionLocal()
    try:
        print(f"--- Evaluation for Query: '{query}' ---")
        
        # 1. Keyword Search
        keyword_results = search_events(db, keyword=query)
        print(f"\n[Keyword Search] Found {keyword_results.total} events")
        for i, ev in enumerate(keyword_results.events[:3]):
            print(f"  {i+1}. {ev.page_title} - {ev.url}")
            
        # 2. Vector Search (Semantic)
        vector_results = search_similar_memories(db, query=query, limit=3)
        print(f"\n[Vector Search] Found {len(vector_results)} memories")
        for i, mem in enumerate(vector_results):
            print(f"  {i+1}. {mem.content}")
            
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Task 5.6: Compare Keyword vs Vector")
    parser.add_argument("query", type=str, help="Search query")
    args = parser.parse_args()
    compare_search(args.query)
