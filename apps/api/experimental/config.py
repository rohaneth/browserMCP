import os
from typing import Dict, Any

def str_to_bool(val: Any, default: bool = True) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes", "on", "t")

class ExperimentalConfig:
    ENABLE_EXPERIMENTAL_WATCHER: bool = str_to_bool(os.getenv("ENABLE_EXPERIMENTAL_WATCHER", "true"), True)
    ENABLE_EXPERIMENTAL_DISCOVERY: bool = str_to_bool(os.getenv("ENABLE_EXPERIMENTAL_DISCOVERY", "true"), True)
    WATCHER_POLL_INTERVAL_SECONDS: int = int(os.getenv("WATCHER_POLL_INTERVAL_SECONDS", "5"))
    WATCHER_EVENT_BATCH_THRESHOLD: int = int(os.getenv("WATCHER_EVENT_BATCH_THRESHOLD", "3"))

config = ExperimentalConfig()
