from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from experimental.config import config
from experimental.watcher import BrowserWatcher

router = APIRouter(prefix="/watcher", tags=["Experimental - Continuous Watcher"])

def check_feature_flag():
    if not config.ENABLE_EXPERIMENTAL_WATCHER:
        raise HTTPException(
            status_code=503,
            detail="Continuous Browser Watcher is currently disabled via feature flag (ENABLE_EXPERIMENTAL_WATCHER=false)."
        )

@router.post("/start")
async def start_watcher(focus: Optional[str] = None):
    """Start continuous background monitoring of incoming browser events."""
    check_feature_flag()
    watcher = BrowserWatcher.get_instance()
    return await watcher.start(focus=focus)

@router.post("/stop")
async def stop_watcher():
    """Stop continuous background monitoring cleanly."""
    check_feature_flag()
    watcher = BrowserWatcher.get_instance()
    return await watcher.stop()

@router.get("/status")
def get_watcher_status():
    """Get current status, observed events count, and alert totals."""
    check_feature_flag()
    watcher = BrowserWatcher.get_instance()
    return watcher.get_status()

@router.get("/events")
def get_watcher_events(limit: int = Query(50, ge=1, le=200)):
    """Get recent alerts and shift triggers discovered by the watcher."""
    check_feature_flag()
    watcher = BrowserWatcher.get_instance()
    return {"alerts": watcher.get_events(limit=limit)}
