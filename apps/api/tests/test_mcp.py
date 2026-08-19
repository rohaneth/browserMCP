import pytest
import json
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mcp')))

from main import app
from auth import verify_token, get_configured_api_key
from tools import (
    execute_investigate,
    execute_search_history,
    execute_get_timeline,
    execute_get_sessions,
    execute_get_domain_statistics,
    execute_compare_time_periods,
    execute_infer_preferences,
    execute_get_behavioral_patterns,
    execute_get_evidence
)

client = TestClient(app)


def test_mcp_health():
    response = client.get("/mcp/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mcp"


def test_mcp_info():
    response = client.get("/mcp/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PersonalBrowserIntelligence"
    assert data["tools_count"] == 9
    assert "tools_list" in data["endpoints"]


def test_mcp_tools_list():
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) == 9
    
    tool_names = [t["name"] for t in data["tools"]]
    expected_tools = [
        "investigate",
        "search_browser_history",
        "get_timeline",
        "get_sessions",
        "get_domain_statistics",
        "compare_time_periods",
        "infer_preferences",
        "get_behavioral_patterns",
        "get_evidence"
    ]
    for exp in expected_tools:
        assert exp in tool_names


def test_mcp_auth_enforcement(monkeypatch):
    monkeypatch.setenv("MCP_API_KEY", "secret-test-token-12345")
    
    # Unauthorized request
    res_unauth = client.get("/mcp/tools")
    assert res_unauth.status_code == 401

    # Authorized request with Bearer
    res_auth = client.get("/mcp/tools", headers={"Authorization": "Bearer secret-test-token-12345"})
    assert res_auth.status_code == 200

    # Authorized request with raw token
    res_auth_raw = client.get("/mcp/tools", headers={"Authorization": "secret-test-token-12345"})
    assert res_auth_raw.status_code == 200


def test_tool_investigate_tool():
    res = client.post("/mcp/tools/call", json={
        "name": "investigate",
        "arguments": {"question": "what is my favourite programming language"}
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "answer" in data
    assert "evidence" in data
    assert "status" in data


def test_tool_search_history():
    res = client.post("/mcp/tools/call", json={
        "name": "search_browser_history",
        "arguments": {"query": "java", "limit": 5}
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "events" in data
    assert "total_matches" in data


def test_tool_get_timeline():
    res = client.post("/mcp/tools/call", json={
        "name": "get_timeline",
        "arguments": {"limit": 10}
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "timeline" in data
    assert "total_count" in data


def test_tool_get_sessions():
    res = client.post("/mcp/tools/call", json={
        "name": "get_sessions",
        "arguments": {"limit": 5}
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "sessions" in data
    assert "total_sessions" in data
    if data["sessions"]:
        s = data["sessions"][0]
        assert "duration_seconds" in s
        assert "dominant_activity" in s


def test_tool_domain_statistics():
    res = client.post("/mcp/tools/call", json={
        "name": "get_domain_statistics",
        "arguments": {"limit": 5}
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "domains" in data
    assert "total_unique_domains" in data


def test_tool_compare_time_periods():
    res = client.post("/mcp/tools/call", json={
        "name": "compare_time_periods",
        "arguments": {
            "period_a_start": "2026-08-16T00:00:00",
            "period_a_end": "2026-08-16T23:59:59",
            "period_b_start": "2026-08-15T00:00:00",
            "period_b_end": "2026-08-15T23:59:59",
            "label_a": "Today",
            "label_b": "Yesterday"
        }
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "comparison" in data
    assert "summary_insights" in data


def test_tool_infer_preferences():
    res = client.post("/mcp/tools/call", json={
        "name": "infer_preferences",
        "arguments": {"category": "programming_language"}
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "category" in data
    assert "confidence" in data
    assert "top_candidate" in data


def test_tool_get_behavioral_patterns():
    res = client.post("/mcp/tools/call", json={
        "name": "get_behavioral_patterns",
        "arguments": {}
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert "hourly_distribution" in data
    assert "weekday_distribution" in data


def test_mcp_json_rpc():
    # Test initialize
    init_res = client.post("/mcp/rpc", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    assert init_res.status_code == 200
    assert init_res.json()["result"]["serverInfo"]["name"] == "PersonalBrowserIntelligence"

    # Test tools/list
    list_res = client.post("/mcp/rpc", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    })
    assert list_res.status_code == 200
    assert len(list_res.json()["result"]["tools"]) == 9

    # Test tools/call
    call_res = client.post("/mcp/rpc", json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "infer_preferences",
            "arguments": {"category": "programming_language"}
        }
    })
    assert call_res.status_code == 200
    assert len(call_res.json()["result"]["content"]) > 0
