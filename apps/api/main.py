import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import events, privacy, timeline, search, memory, ws

app = FastAPI(
    title="Browser Agent API",
    description="API for ingesting and querying browser events.",
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

app.include_router(ws.router)
app.include_router(events.router, prefix="/api/v1")
app.include_router(privacy.router, prefix="/api/v1/privacy")
app.include_router(timeline.router)
app.include_router(search.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"status": "ok", "service": "api"}
