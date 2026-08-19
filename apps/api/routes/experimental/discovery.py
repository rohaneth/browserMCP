from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from experimental.config import config
from experimental.discovery import BrowserSelfDiscovery

router = APIRouter(prefix="/discovery", tags=["Experimental - Self Discovery"])

def check_feature_flag():
    if not config.ENABLE_EXPERIMENTAL_DISCOVERY:
        raise HTTPException(
            status_code=503,
            detail="Browser Self-Discovery is currently disabled via feature flag (ENABLE_EXPERIMENTAL_DISCOVERY=false)."
        )

@router.post("/run")
def run_self_discovery(focus_hint: Optional[str] = None):
    """
    Trigger an autonomous self-discovery run over captured browser activity.
    Generates hypotheses, verifies evidence, and returns discoveries.
    """
    check_feature_flag()
    return BrowserSelfDiscovery.run_discovery(focus_hint=focus_hint)

@router.get("/results")
def get_discovery_results(limit: int = Query(20, ge=1, le=100)):
    """Retrieve all evidence-backed discoveries across runs."""
    check_feature_flag()
    results = BrowserSelfDiscovery.get_results(limit=limit)
    return {"total": len(results), "discoveries": results}

@router.get("/{discovery_id}")
def get_discovery_by_id(discovery_id: str):
    """Retrieve a specific discovery and its complete supporting evidence."""
    check_feature_flag()
    res = BrowserSelfDiscovery.get_discovery_by_id(discovery_id)
    if not res:
        raise HTTPException(status_code=404, detail="Discovery result not found.")
    return res
