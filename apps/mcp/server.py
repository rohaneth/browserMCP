import sys
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
import mcp.types as types
from mcp.server.lowlevel import Server

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api')))

from tools import (
    execute_investigate,
    execute_search_history,
    execute_get_timeline,
    execute_get_sessions,
    execute_get_domain_statistics,
    compare_time_periods,
    execute_infer_preferences,
    execute_get_behavioral_patterns,
    execute_get_evidence,
    execute_classify_browser_event,
    execute_get_interest_clusters,
    execute_get_behavioral_anomalies,
    execute_get_content_recommendations,
    execute_agentic_investigate,
    execute_lyzr_orchestrated_investigate
)
from auth import verify_token

server = Server("PersonalBrowserIntelligence")

# Define All 9 Composable Tools
TOOLS: List[types.Tool] = [
    types.Tool(
        name="investigate",
        description="Main general-purpose investigation tool for arbitrary, open-ended or complex questions about user browsing activity. Uses multi-signal retrieval, dynamic preference inference, anti-hallucination guardrails, and classifies conclusions into CONFIRMED, LIKELY, or UNKNOWN with attached verifiable evidence IDs.",
        inputSchema={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The natural language question to investigate from browsing data (e.g., 'favourite programming language', 'what I searched on Stack Overflow', 'why Java appears to be my favourite', 'what I did yesterday afternoon', 'longest session last week')."
                }
            },
            "required": ["question"]
        }
    ),
    types.Tool(
        name="search_browser_history",
        description="Search across browser history events, page titles, URLs, typed inputs, and extracted page contents with optional domain, date/time, and event type filtering.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keyword or text search query."
                },
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter (e.g. 'stackoverflow.com', 'github.com')."
                },
                "start_time": {
                    "type": "string",
                    "description": "Optional start time filter (ISO format or YYYY-MM-DD)."
                },
                "end_time": {
                    "type": "string",
                    "description": "Optional end time filter (ISO format or YYYY-MM-DD)."
                },
                "event_type": {
                    "type": "string",
                    "description": "Optional event type filter (e.g. 'search_submitted', 'page_loaded')."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of events to return (default: 20).",
                    "default": 20
                }
            },
            "required": ["query"]
        }
    ),
    types.Tool(
        name="get_timeline",
        description="Retrieve a chronological sequence of browser events with timestamps, page titles, URLs, domains, and typed inputs. Useful for inspecting sequential activity during specific time windows.",
        inputSchema={
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": "Optional ISO timestamp or date to filter after."
                },
                "end_time": {
                    "type": "string",
                    "description": "Optional ISO timestamp or date to filter before."
                },
                "domain": {
                    "type": "string",
                    "description": "Optional domain filter."
                },
                "event_type": {
                    "type": "string",
                    "description": "Optional event type filter."
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of events to retrieve (default: 50).",
                    "default": 50
                },
                "offset": {
                    "type": "integer",
                    "description": "Pagination offset (default: 0).",
                    "default": 0
                }
            }
        }
    ),
    types.Tool(
        name="get_sessions",
        description="Retrieve and analyze browser sessions. Computes session durations, active domain distribution, search queries, key page loads, event counts, and dominant activity for each session.",
        inputSchema={
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": "Optional start time filter."
                },
                "end_time": {
                    "type": "string",
                    "description": "Optional end time filter."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of sessions to return (default: 20).",
                    "default": 20
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional UUID of a specific session to inspect."
                }
            }
        }
    ),
    types.Tool(
        name="get_domain_statistics",
        description="Calculate visit statistics across domains: visit frequencies, unique pages viewed, search queries conducted per domain, and first/last seen timestamps.",
        inputSchema={
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": "Optional start time filter."
                },
                "end_time": {
                    "type": "string",
                    "description": "Optional end time filter."
                },
                "limit": {
                    "type": "integer",
                    "description": "Top N domains to return (default: 20).",
                    "default": 20
                },
                "domain": {
                    "type": "string",
                    "description": "Optional specific domain filter."
                }
            }
        }
    ),
    types.Tool(
        name="compare_time_periods",
        description="Compare browsing patterns, domain shifts, search activity, and session metrics between two distinct time periods (e.g. this week vs last week).",
        inputSchema={
            "type": "object",
            "properties": {
                "period_a_start": {
                    "type": "string",
                    "description": "Start timestamp for Period A (ISO format)."
                },
                "period_a_end": {
                    "type": "string",
                    "description": "End timestamp for Period A (ISO format)."
                },
                "period_b_start": {
                    "type": "string",
                    "description": "Start timestamp for Period B (ISO format)."
                },
                "period_b_end": {
                    "type": "string",
                    "description": "End timestamp for Period B (ISO format)."
                },
                "label_a": {
                    "type": "string",
                    "description": "Friendly label for Period A (default: 'Period A').",
                    "default": "Period A"
                },
                "label_b": {
                    "type": "string",
                    "description": "Friendly label for Period B (default: 'Period B').",
                    "default": "Period B"
                }
            },
            "required": ["period_a_start", "period_a_end", "period_b_start", "period_b_end"]
        }
    ),
    types.Tool(
        name="infer_preferences",
        description="Perform dynamic preference & interest inference across programming languages, comedians, entertainment, or general topics based on weighted frequency and search signals in browser history.",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional category ('programming_language', 'comedian', 'movies_entertainment', 'topics_interests')."
                },
                "query": {
                    "type": "string",
                    "description": "Optional natural language hint to automatically detect category."
                }
            }
        }
    ),
    types.Tool(
        name="get_behavioral_patterns",
        description="Analyze behavioral patterns across browsing history: hourly activity breakdown, weekday distributions, peak browsing hours, and top interaction types.",
        inputSchema={
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": "Optional start time filter."
                },
                "end_time": {
                    "type": "string",
                    "description": "Optional end time filter."
                }
            }
        }
    ),
    types.Tool(
        name="get_evidence",
        description="Retrieve raw, sanitized evidence records for specific event UUIDs. Ensures total auditability and anti-hallucination verification without leaking sensitive secrets.",
        inputSchema={
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
    ),
    types.Tool(
        name="classify_browser_event",
        description="ML-powered browser event classifier that categorizes web activity (programming/development, education, research, entertainment, shopping, social, news, finance, travel, other) with probability scores.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text content or search term to classify."},
                "page_title": {"type": "string", "description": "Optional page title."},
                "url": {"type": "string", "description": "Optional URL."},
                "domain": {"type": "string", "description": "Optional domain name."}
            },
            "required": ["text"]
        }
    ),
    types.Tool(
        name="get_interest_clusters",
        description="Unsupervised ML interest discovery using dense embeddings and K-Means clustering to extract semantic user interest groups and keyword profiles.",
        inputSchema={
            "type": "object",
            "properties": {
                "n_clusters": {"type": "integer", "description": "Number of interest clusters to discover (default: 5).", "default": 5},
                "min_samples": {"type": "integer", "description": "Minimum event samples required.", "default": 3}
            }
        }
    ),
    types.Tool(
        name="get_behavioral_anomalies",
        description="ML-based behavioral anomaly detection using Isolation Forest to identify unusual browsing hours, rare domains, and anomalous interaction patterns.",
        inputSchema={
            "type": "object",
            "properties": {
                "contamination": {"type": "number", "description": "Expected anomaly contamination proportion (default: 0.05).", "default": 0.05},
                "limit": {"type": "integer", "description": "Max anomalies to return (default: 10).", "default": 10}
            }
        }
    ),
    types.Tool(
        name="get_content_recommendations",
        description="Content-based recommendation engine suggesting research topics, articles, and learning paths aligned with inferred user interest clusters.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of recommendations (default: 5).", "default": 5}
            }
        }
    ),
    types.Tool(
        name="agentic_investigate",
        description="Iterative, multi-step Agentic Investigation engine with step budget, tool calling trace, loop protection, and structured machine-readable conclusion.",
        inputSchema={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Complex or multi-hop natural language question to investigate."},
                "max_iterations": {"type": "integer", "description": "Maximum agent step budget (default: 4).", "default": 4}
            },
            "required": ["question"]
        }
    ),
    types.Tool(
        name="lyzr_orchestrated_investigate",
        description="Higher-level Lyzr AI Agent orchestration layer coordinating all underlying MCP investigation tools with evidence grounding.",
        inputSchema={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Natural language question for Lyzr Agent to investigate."},
                "user_id": {"type": "string", "description": "Optional user identifier.", "default": "default_user"}
            },
            "required": ["question"]
        }
    )
]


async def handle_list_tools(params: Optional[types.PaginatedRequestParams] = None, req_ctx=None) -> types.ListToolsResult:
    """Returns the list of available MCP tools."""
    return types.ListToolsResult(tools=TOOLS)


async def handle_call_tool(params: types.CallToolRequestParams, req_ctx=None) -> types.CallToolResult:
    """Executes the requested tool and returns structured text content."""
    name = params.name
    arguments = params.arguments or {}
    try:
        if name == "investigate":
            question = arguments.get("question", "")
            res = execute_investigate(question=question)
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "search_browser_history":
            res = execute_search_history(
                query=arguments.get("query", ""),
                domain=arguments.get("domain"),
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                event_type=arguments.get("event_type"),
                limit=arguments.get("limit", 20)
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "get_timeline":
            res = execute_get_timeline(
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                domain=arguments.get("domain"),
                event_type=arguments.get("event_type"),
                limit=arguments.get("limit", 50),
                offset=arguments.get("offset", 0)
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "get_sessions":
            res = execute_get_sessions(
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                limit=arguments.get("limit", 20),
                session_id=arguments.get("session_id")
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "get_domain_statistics":
            res = execute_get_domain_statistics(
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time"),
                limit=arguments.get("limit", 20),
                domain=arguments.get("domain")
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "compare_time_periods":
            res = execute_compare_time_periods(
                period_a_start=arguments.get("period_a_start", ""),
                period_a_end=arguments.get("period_a_end", ""),
                period_b_start=arguments.get("period_b_start", ""),
                period_b_end=arguments.get("period_b_end", ""),
                label_a=arguments.get("label_a", "Period A"),
                label_b=arguments.get("label_b", "Period B")
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "infer_preferences":
            res = execute_infer_preferences(
                category=arguments.get("category"),
                query=arguments.get("query")
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "get_behavioral_patterns":
            res = execute_get_behavioral_patterns(
                start_time=arguments.get("start_time"),
                end_time=arguments.get("end_time")
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "get_evidence":
            evidence_ids = arguments.get("evidence_ids", [])
            res = execute_get_evidence(evidence_ids=evidence_ids)
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "classify_browser_event":
            res = execute_classify_browser_event(
                text=arguments.get("text", ""),
                page_title=arguments.get("page_title"),
                url=arguments.get("url"),
                domain=arguments.get("domain")
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "get_interest_clusters":
            res = execute_get_interest_clusters(
                n_clusters=arguments.get("n_clusters", 5),
                min_samples=arguments.get("min_samples", 3)
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "get_behavioral_anomalies":
            res = execute_get_behavioral_anomalies(
                contamination=arguments.get("contamination", 0.05),
                limit=arguments.get("limit", 10)
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "get_content_recommendations":
            res = execute_get_content_recommendations(
                limit=arguments.get("limit", 5)
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "agentic_investigate":
            res = execute_agentic_investigate(
                question=arguments.get("question", ""),
                max_iterations=arguments.get("max_iterations", 4)
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        elif name == "lyzr_orchestrated_investigate":
            res = execute_lyzr_orchestrated_investigate(
                question=arguments.get("question", ""),
                user_id=arguments.get("user_id", "default_user")
            )
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(res, indent=2))])

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        error_payload = {
            "error": True,
            "tool": name,
            "message": str(e)
        }
        return types.CallToolResult(
            isError=True,
            content=[types.TextContent(type="text", text=json.dumps(error_payload, indent=2))]
        )


# Register MCP Handlers
server.add_request_handler("tools/list", types.PaginatedRequestParams, handle_list_tools)
server.add_request_handler("tools/call", types.CallToolRequestParams, handle_call_tool)


def get_server_capabilities() -> types.ServerCapabilities:
    return types.ServerCapabilities(
        tools=types.ToolsCapability(listChanged=False)
    )


async def run_stdio():
    """Runs the MCP server over standard stdio."""
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            types.InitializationOptions(
                server_name="PersonalBrowserIntelligence",
                server_version="1.0.0",
                capabilities=get_server_capabilities(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run_stdio())
