import asyncio
import sys
import os

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api')))

from db.session import SessionLocal
from services.search import search_events, search_hybrid
from services.memory import search_similar_memories
from mcp.server import FastMCP

mcp = FastMCP("PersonalBrowserIntelligence")

@mcp.tool()
def search_browser_events(query: str, limit: int = 5) -> str:
    """Search for browser events using a keyword query."""
    db = SessionLocal()
    try:
        res = search_events(db, query)
        results = [f"{ev.page_title} - {ev.url}" for ev in res.events[:limit]]
        return "\n".join(results) if results else "No events found."
    finally:
        db.close()

@mcp.tool()
def get_timeline(limit: int = 10) -> str:
    """Get the recent timeline of user activity."""
    db = SessionLocal()
    try:
        from models.events import Event
        events = db.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()
        results = [f"[{ev.timestamp}] {ev.event_type}: {ev.page_title} ({ev.domain})" for ev in events]
        return "\n".join(results) if results else "No recent activity."
    finally:
        db.close()

@mcp.tool()
def search_browser_memory(query: str, limit: int = 5) -> str:
    """Semantic search over user's extracted memories."""
    db = SessionLocal()
    try:
        memories = search_similar_memories(db, query, limit)
        results = [m.content for m in memories]
        return "\n".join(results) if results else "No memories found."
    finally:
        db.close()

if __name__ == "__main__":
    mcp.run()
