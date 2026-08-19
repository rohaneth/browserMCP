import sys
import os
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, HTTPException, Header, Query, Depends
from fastapi.responses import JSONResponse

mcp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mcp'))
if mcp_dir not in sys.path:
    sys.path.insert(0, mcp_dir)

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

router = APIRouter(prefix="/mcp", tags=["MCP Server"])

MCP_TOOL_METADATA = [
    {
        "name": "investigate",
        "description": "Main general-purpose investigation tool for arbitrary, open-ended or complex questions about user browsing activity. Uses multi-signal retrieval, dynamic preference inference, anti-hallucination guardrails, and classifies conclusions into CONFIRMED, LIKELY, or UNKNOWN with attached verifiable evidence IDs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The natural language question to investigate from browsing data (e.g., 'favourite programming language', 'what I searched on Stack Overflow', 'why Java appears to be my favourite', 'what I did yesterday afternoon', 'longest session last week')."
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "search_browser_history",
        "description": "Search across browser history events, page titles, URLs, typed inputs, and extracted page contents with optional domain, date/time, and event type filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword or text search query."},
                "domain": {"type": "string", "description": "Optional domain filter (e.g. 'stackoverflow.com', 'github.com')."},
                "start_time": {"type": "string", "description": "Optional start time filter (ISO format or YYYY-MM-DD)."},
                "end_time": {"type": "string", "description": "Optional end time filter (ISO format or YYYY-MM-DD)."},
                "event_type": {"type": "string", "description": "Optional event type filter (e.g. 'search_submitted', 'page_loaded')."},
                "limit": {"type": "integer", "description": "Maximum number of events to return (default: 20).", "default": 20}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_timeline",
        "description": "Retrieve a chronological sequence of browser events with timestamps, page titles, URLs, domains, and typed inputs. Useful for inspecting sequential activity during specific time windows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_time": {"type": "string", "description": "Optional ISO timestamp or date to filter after."},
                "end_time": {"type": "string", "description": "Optional ISO timestamp or date to filter before."},
                "domain": {"type": "string", "description": "Optional domain filter."},
                "event_type": {"type": "string", "description": "Optional event type filter."},
                "limit": {"type": "integer", "description": "Number of events to retrieve (default: 50).", "default": 50},
                "offset": {"type": "integer", "description": "Pagination offset (default: 0).", "default": 0}
            }
        }
    },
    {
        "name": "get_sessions",
        "description": "Retrieve and analyze browser sessions. Computes session durations, active domain distribution, search queries, key page loads, event counts, and dominant activity for each session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_time": {"type": "string", "description": "Optional start time filter."},
                "end_time": {"type": "string", "description": "Optional end time filter."},
                "limit": {"type": "integer", "description": "Maximum number of sessions to return (default: 20).", "default": 20},
                "session_id": {"type": "string", "description": "Optional UUID of a specific session to inspect."}
            }
        }
    },
    {
        "name": "get_domain_statistics",
        "description": "Calculate visit statistics across domains: visit frequencies, unique pages viewed, search queries conducted per domain, and first/last seen timestamps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_time": {"type": "string", "description": "Optional start time filter."},
                "end_time": {"type": "string", "description": "Optional end time filter."},
                "limit": {"type": "integer", "description": "Top N domains to return (default: 20).", "default": 20},
                "domain": {"type": "string", "description": "Optional specific domain filter."}
            }
        }
    },
    {
        "name": "compare_time_periods",
        "description": "Compare browsing patterns, domain shifts, search activity, and session metrics between two distinct time periods (e.g. this week vs last week).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period_a_start": {"type": "string", "description": "Start timestamp for Period A (ISO format)."},
                "period_a_end": {"type": "string", "description": "End timestamp for Period A (ISO format)."},
                "period_b_start": {"type": "string", "description": "Start timestamp for Period B (ISO format)."},
                "period_b_end": {"type": "string", "description": "End timestamp for Period B (ISO format)."},
                "label_a": {"type": "string", "description": "Friendly label for Period A (default: 'Period A').", "default": "Period A"},
                "label_b": {"type": "string", "description": "Friendly label for Period B (default: 'Period B').", "default": "Period B"}
            },
            "required": ["period_a_start", "period_a_end", "period_b_start", "period_b_end"]
        }
    },
    {
        "name": "infer_preferences",
        "description": "Perform dynamic preference & interest inference across programming languages, comedians, entertainment, or general topics based on weighted frequency and search signals in browser history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Optional category ('programming_language', 'comedian', 'movies_entertainment', 'topics_interests')."},
                "query": {"type": "string", "description": "Optional natural language hint to automatically detect category."}
            }
        }
    },
    {
        "name": "get_behavioral_patterns",
        "description": "Analyze behavioral patterns across browsing history: hourly activity breakdown, weekday distributions, peak browsing hours, and top interaction types.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_time": {"type": "string", "description": "Optional start time filter."},
                "end_time": {"type": "string", "description": "Optional end time filter."}
            }
        }
    },
    {
        "name": "get_evidence",
        "description": "Retrieve raw, sanitized evidence records for specific event UUIDs. Ensures total auditability and anti-hallucination verification without leaking sensitive secrets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "evidence_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of UUID strings for events."
                }
            },
            "required": ["evidence_ids"]
        }
    }
]


def check_auth(authorization: Optional[str] = Header(None)):
    """Validates authorization header against configured MCP_API_KEY."""
    if not verify_token(authorization):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing MCP Authorization Bearer token."
        )


@router.get("/health")
def mcp_health():
    """Health check endpoint for the MCP service."""
    return {
        "status": "healthy",
        "service": "mcp",
        "version": "1.0.0",
        "auth_enabled": bool(get_configured_api_key())
    }


@router.get("/info")
def mcp_info():
    """MCP Service discovery and metadata endpoint."""
    return {
        "name": "PersonalBrowserIntelligence",
        "protocol_version": "2024-11-05",
        "version": "1.0.0",
        "description": "Personal Browser Intelligence MCP Server for natural language querying over browser activity.",
        "auth_required": bool(get_configured_api_key()),
        "endpoints": {
            "tools_list": "/mcp/tools",
            "tool_call": "/mcp/tools/call",
            "rpc": "/mcp/rpc"
        },
        "tools_count": len(MCP_TOOL_METADATA)
    }


@router.get("/tools", dependencies=[Depends(check_auth)])
def list_mcp_tools():
    """Returns all registered MCP tools and JSON schemas."""
    return {
        "tools": MCP_TOOL_METADATA
    }


@router.post("/tools/call", dependencies=[Depends(check_auth)])
async def call_mcp_tool(request: Request):
    """
    Executes an MCP tool with provided arguments and returns JSON response.
    Request body: {"name": "<tool_name>", "arguments": {...}}
    """
    body = await request.json()
    name = body.get("name")
    arguments = body.get("arguments", {})

    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name' field in tool call request.")

    try:
        if name == "investigate":
            res = execute_investigate(question=arguments.get("question", ""))
        elif name == "search_browser_history":
            res = execute_search_history(
                query=arguments.get("query", ""),
                domain=arguments.get("domain"),
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                event_type=arguments.get("event_type"),
                limit=arguments.get("limit", 20)
            )
        elif name == "get_timeline":
            res = execute_get_timeline(
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                domain=arguments.get("domain"),
                event_type=arguments.get("event_type"),
                limit=arguments.get("limit", 50),
                offset=arguments.get("offset", 0)
            )
        elif name == "get_sessions":
            res = execute_get_sessions(
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                limit=arguments.get("limit", 20),
                session_id=arguments.get("session_id")
            )
        elif name == "get_domain_statistics":
            res = execute_get_domain_statistics(
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                limit=arguments.get("limit", 20),
                domain=arguments.get("domain")
            )
        elif name == "compare_time_periods":
            res = execute_compare_time_periods(
                period_a_start=arguments.get("period_a_start", ""),
                period_a_end=arguments.get("period_a_end", ""),
                period_b_start=arguments.get("period_b_start", ""),
                period_b_end=arguments.get("period_b_end", ""),
                label_a=arguments.get("label_a", "Period A"),
                label_b=arguments.get("label_b", "Period B")
            )
        elif name == "infer_preferences":
            res = execute_infer_preferences(
                category=arguments.get("category"),
                query=arguments.get("query")
            )
        elif name == "get_behavioral_patterns":
            res = execute_get_behavioral_patterns(
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time")
            )
        elif name == "get_evidence":
            res = execute_get_evidence(
                evidence_ids=arguments.get("evidence_ids", [])
            )
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res, indent=2)
                }
            ],
            "data": res
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"error": True, "message": str(e)}, indent=2)
                    }
                ]
            }
        )


@router.post("/rpc", dependencies=[Depends(check_auth)])
async def mcp_json_rpc(request: Request):
    """
    Standard JSON-RPC 2.0 endpoint for MCP protocol clients.
    Supports initialize, tools/list, and tools/call.
    """
    body = await request.json()
    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "PersonalBrowserIntelligence",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return JSONResponse(status_code=204, content=None)

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOL_METADATA
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        # Simulate call_mcp_tool
        dummy_req = Request(scope=request.scope)
        # Directly invoke execution
        try:
            if tool_name == "investigate":
                res = execute_investigate(question=tool_args.get("question", ""))
            elif tool_name == "search_browser_history":
                res = execute_search_history(
                    query=tool_args.get("query", ""),
                    domain=tool_args.get("domain"),
                    start_time=tool_args.get("start_time"),
                    end_time=tool_args.get("end_time"),
                    event_type=tool_args.get("event_type"),
                    limit=tool_args.get("limit", 20)
                )
            elif tool_name == "get_timeline":
                res = execute_get_timeline(
                    start_time=tool_args.get("start_time"),
                    end_time=tool_args.get("end_time"),
                    domain=tool_args.get("domain"),
                    event_type=tool_args.get("event_type"),
                    limit=tool_args.get("limit", 50),
                    offset=tool_args.get("offset", 0)
                )
            elif tool_name == "get_sessions":
                res = execute_get_sessions(
                    start_time=tool_args.get("start_time"),
                    end_time=tool_args.get("end_time"),
                    limit=tool_args.get("limit", 20),
                    session_id=tool_args.get("session_id")
                )
            elif tool_name == "get_domain_statistics":
                res = execute_get_domain_statistics(
                    start_time=tool_args.get("start_time"),
                    end_time=tool_args.get("end_time"),
                    limit=tool_args.get("limit", 20),
                    domain=tool_args.get("domain")
                )
            elif tool_name == "compare_time_periods":
                res = execute_compare_time_periods(
                    period_a_start=tool_args.get("period_a_start", ""),
                    period_a_end=tool_args.get("period_a_end", ""),
                    period_b_start=tool_args.get("period_b_start", ""),
                    period_b_end=tool_args.get("period_b_end", ""),
                    label_a=tool_args.get("label_a", "Period A"),
                    label_b=tool_args.get("label_b", "Period B")
                )
            elif tool_name == "infer_preferences":
                res = execute_infer_preferences(
                    category=tool_args.get("category"),
                    query=tool_args.get("query")
                )
            elif tool_name == "get_behavioral_patterns":
                res = execute_get_behavioral_patterns(
                    start_time=tool_args.get("start_time"),
                    end_time=tool_args.get("end_time")
                )
            elif tool_name == "get_evidence":
                res = execute_get_evidence(
                    evidence_ids=tool_args.get("evidence_ids", [])
                )
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method/Tool '{tool_name}' not found"}
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"error": True, "message": str(e)}, indent=2)
                        }
                    ]
                }
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unhandled method: {method}"}
    }
