import pytest
import json
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from experimental.config import config
from experimental.watcher import BrowserWatcher

client = TestClient(app)

def test_watcher_lifecycle_and_status():
    # 1. Get status
    res_status = client.get("/api/v1/experimental/watcher/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "is_running" in data
    assert "total_events_observed" in data

    # 2. Start watcher
    res_start = client.post("/api/v1/experimental/watcher/start?focus=Test%20monitoring")
    assert res_start.status_code == 200
    assert res_start.json()["status"] in ["started", "already_running"]

    # 3. Check status is now running
    res_status_after = client.get("/api/v1/experimental/watcher/status")
    assert res_status_after.json()["is_running"] is True

    # 4. Get events
    res_events = client.get("/api/v1/experimental/watcher/events")
    assert res_events.status_code == 200
    assert "alerts" in res_events.json()

    # 5. Stop watcher
    res_stop = client.post("/api/v1/experimental/watcher/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "stopped"

    # 6. Verify stopped
    res_final = client.get("/api/v1/experimental/watcher/status")
    assert res_final.json()["is_running"] is False


def test_self_discovery_run_and_results():
    # 1. Trigger a discovery run
    res_run = client.post("/api/v1/experimental/discovery/run?focus_hint=Find%20unusual%20patterns")
    assert res_run.status_code == 200
    data = res_run.json()
    assert data["status"] == "completed"
    assert "run_id" in data
    assert "discoveries" in data

    # 2. Get list of discoveries
    res_results = client.get("/api/v1/experimental/discovery/results")
    assert res_results.status_code == 200
    res_data = res_results.json()
    assert res_data["total"] >= 1
    first_discovery = res_data["discoveries"][0]
    assert "category" in first_discovery
    assert "hypothesis" in first_discovery
    assert "confidence" in first_discovery
    assert "supporting_evidence" in first_discovery

    # 3. Get single discovery by ID
    disc_id = first_discovery["id"]
    res_single = client.get(f"/api/v1/experimental/discovery/{disc_id}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == disc_id


def test_feature_flag_disable(monkeypatch):
    # Disable watcher
    monkeypatch.setattr(config, "ENABLE_EXPERIMENTAL_WATCHER", False)
    res_w = client.get("/api/v1/experimental/watcher/status")
    assert res_w.status_code == 503
    assert "disabled" in res_w.json()["detail"].lower()

    # Disable discovery
    monkeypatch.setattr(config, "ENABLE_EXPERIMENTAL_DISCOVERY", False)
    res_d = client.post("/api/v1/experimental/discovery/run")
    assert res_d.status_code == 503
    assert "disabled" in res_d.json()["detail"].lower()
