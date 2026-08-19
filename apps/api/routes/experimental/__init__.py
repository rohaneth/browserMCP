from fastapi import APIRouter
from .watcher import router as watcher_router
from .discovery import router as discovery_router

router = APIRouter(prefix="/api/v1/experimental", tags=["Experimental Features"])

router.include_router(watcher_router)
router.include_router(discovery_router)
