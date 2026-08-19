import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes import events, privacy, timeline, search, memory, ws, mcp
from services.sync_log import sync_events_log_to_db

app = FastAPI(
    title="Browser Agent API",
    description="API for ingesting and querying browser events with integrated MCP Server.",
    version="1.0.0",
)

# For local development, allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auto_sync_events_log_middleware(request: Request, call_next):
    """
    Automatically checks if events.log was modified and synchronizes
    new events into the database on incoming requests.
    """
    try:
        sync_events_log_to_db()
    except Exception:
        pass
    response = await call_next(request)
    return response


@app.on_event("startup")
def on_startup():
    """Initial synchronization of events.log on server boot."""
    try:
        sync_events_log_to_db(force=True)
    except Exception:
        pass


app.include_router(ws.router)
app.include_router(events.router, prefix="/api/v1")
app.include_router(privacy.router, prefix="/api/v1/privacy")
app.include_router(timeline.router)
app.include_router(search.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(mcp.router)

# Mount isolated experimental features (Watcher & Self-Discovery)
try:
    from routes.experimental import router as experimental_router
    app.include_router(experimental_router)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Experimental features disabled or failed to load: {e}")


@app.get("/")
def read_root():
    return {"status": "ok", "service": "api"}
