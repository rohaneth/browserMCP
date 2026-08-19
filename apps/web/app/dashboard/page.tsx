"use client";

import React, { useState, useEffect } from "react";
import Head from "next/head";

interface Evidence {
  event_id: string;
  timestamp: string;
  url?: string;
  title?: string;
  snippet: string;
  relevance: number;
}

interface QueryResult {
  answer: string;
  evidence: Evidence[];
}

interface DiscoveryItem {
  id: string;
  category: string;
  hypothesis: string;
  confidence: string;
  narrative: string;
  supporting_evidence?: any[];
}

interface WatcherStatus {
  is_running: boolean;
  total_events_observed: number;
  total_alerts_triggered: number;
  active_focus: string;
  last_processed_timestamp?: string;
}

interface MCPTool {
  name: string;
  description: string;
  inputSchema?: any;
}

interface TimelineEvent {
  event_id: string;
  timestamp: string;
  domain?: string;
  page_title?: string;
  url?: string;
  input_text?: string;
  event_type: string;
}

export default function DashboardPage() {
  const [apiUrl, setApiUrl] = useState("http://localhost:8000");

  // Ask input & response
  const [askQuery, setAskQuery] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [askResult, setAskResult] = useState<QueryResult | null>(null);
  const [askError, setAskError] = useState<string | null>(null);

  // System Stats
  const [stats, setStats] = useState({
    totalEvents: 0,
    uniqueDomains: 0,
    searchCount: 0,
    sessionsCount: 0,
  });

  // Timeline events for activity chart
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);

  // Discovery / Insights
  const [discoveries, setDiscoveries] = useState<DiscoveryItem[]>([]);
  const [isRunningDiscovery, setIsRunningDiscovery] = useState(false);
  const [selectedDiscovery, setSelectedDiscovery] = useState<DiscoveryItem | null>(null);

  // Watcher
  const [watcherStatus, setWatcherStatus] = useState<WatcherStatus | null>(null);
  const [watcherAlerts, setWatcherAlerts] = useState<any[]>([]);
  const [isTogglingWatcher, setIsTogglingWatcher] = useState(false);

  // MCP
  const [mcpInfo, setMcpInfo] = useState<any>(null);
  const [mcpTools, setMcpTools] = useState<MCPTool[]>([]);
  const [mcpTestResult, setMcpTestResult] = useState<string | null>(null);
  const [isTestingMcp, setIsTestingMcp] = useState(false);

  // Recent Investigations
  const [recentInvs, setRecentInvs] = useState<any[]>([]);

  // Expandable evidence state
  const [expandedEvidence, setExpandedEvidence] = useState(false);

  useEffect(() => {
    if (process.env.NEXT_PUBLIC_API_URL) {
      setApiUrl(process.env.NEXT_PUBLIC_API_URL);
    }
  }, []);

  const loadAllData = async () => {
    const base = apiUrl;

    // 1. Fetch Timeline Events
    try {
      const res = await fetch(`${base}/api/v1/timeline?limit=100`);
      if (res.ok) {
        const data = await res.json();
        const evs: TimelineEvent[] = data.events || [];
        setTimelineEvents(evs);
        
        const domains = new Set(evs.map(e => e.domain).filter(Boolean));
        const searches = evs.filter(e => e.input_text || e.event_type === "search_submitted");
        const sessions = new Set(evs.map((e: any) => e.session_id).filter(Boolean));

        setStats({
          totalEvents: data.total_count || evs.length,
          uniqueDomains: domains.size,
          searchCount: searches.length,
          sessionsCount: Math.max(sessions.size, 1),
        });
      }
    } catch (e) {
      console.error("Timeline error:", e);
    }

    // 2. Fetch Discovery Results
    try {
      const res = await fetch(`${base}/api/v1/experimental/discovery/results?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setDiscoveries(data.discoveries || []);
      }
    } catch (e) {
      console.error("Discovery error:", e);
    }

    // 3. Fetch Watcher Status & Events
    try {
      const resStatus = await fetch(`${base}/api/v1/experimental/watcher/status`);
      if (resStatus.ok) {
        const data = await resStatus.json();
        setWatcherStatus(data);
      }
      const resAlerts = await fetch(`${base}/api/v1/experimental/watcher/events?limit=5`);
      if (resAlerts.ok) {
        const data = await resAlerts.json();
        setWatcherAlerts(data.alerts || []);
      }
    } catch (e) {
      console.error("Watcher error:", e);
    }

    // 4. Fetch MCP Info & Tools
    try {
      const resInfo = await fetch(`${base}/mcp/info`);
      if (resInfo.ok) {
        const data = await resInfo.json();
        setMcpInfo(data);
      }
      const resTools = await fetch(`${base}/mcp/tools`);
      if (resTools.ok) {
        const data = await resTools.json();
        setMcpTools(data.tools || []);
      }
    } catch (e) {
      console.error("MCP error:", e);
    }

    // 5. Fetch Recent Investigations
    try {
      const resInvs = await fetch(`${base}/api/v1/investigations/recent?limit=5`);
      if (resInvs.ok) {
        const data = await resInvs.json();
        setRecentInvs(data || []);
      }
    } catch (e) {
      console.error("Investigations error:", e);
    }
  };

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 15000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  const handleAskSubmit = async (e?: React.FormEvent, presetQuery?: string) => {
    if (e) e.preventDefault();
    const queryToRun = presetQuery || askQuery;
    if (!queryToRun.trim() || isAsking) return;

    if (presetQuery) setAskQuery(presetQuery);
    setIsAsking(true);
    setAskError(null);
    setAskResult(null);

    try {
      const res = await fetch(`${apiUrl}/api/v1/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: queryToRun }),
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      setAskResult(data);
      loadAllData(); // Refresh recent investigations
    } catch (err: any) {
      setAskError(err.message || "Failed to execute investigation.");
    } finally {
      setIsAsking(false);
    }
  };

  const handleToggleWatcher = async () => {
    setIsTogglingWatcher(true);
    try {
      const action = watcherStatus?.is_running ? "stop" : "start";
      const res = await fetch(`${apiUrl}/api/v1/experimental/watcher/${action}`, {
        method: "POST",
      });
      if (res.ok) {
        await loadAllData();
      }
    } catch (err) {
      console.error("Failed to toggle watcher:", err);
    } finally {
      setIsTogglingWatcher(false);
    }
  };

  const handleTriggerDiscovery = async () => {
    setIsRunningDiscovery(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/experimental/discovery/run`, {
        method: "POST",
      });
      if (res.ok) {
        await loadAllData();
      }
    } catch (err) {
      console.error("Failed to run self-discovery:", err);
    } finally {
      setIsRunningDiscovery(false);
    }
  };

  const handleTestMcp = async () => {
    setIsTestingMcp(true);
    setMcpTestResult(null);
    try {
      const res = await fetch(`${apiUrl}/mcp/tools/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "infer_preferences",
          arguments: { category: "programming_language" }
        })
      });
      if (res.ok) {
        const data = await res.json();
        setMcpTestResult(data.data ? `Result: ${data.data.narrative}` : "Tool executed successfully.");
      } else {
        setMcpTestResult(`MCP Error: HTTP ${res.status}`);
      }
    } catch (err: any) {
      setMcpTestResult(`Test failed: ${err.message}`);
    } finally {
      setIsTestingMcp(false);
    }
  };

  // Compute simple activity histogram (hourly buckets)
  const hourlyActivity: { [hour: string]: number } = {};
  for (let i = 0; i < 24; i++) {
    hourlyActivity[`${i < 10 ? '0' : ''}${i}:00`] = 0;
  }
  timelineEvents.forEach((ev) => {
    if (ev.timestamp) {
      const h = new Date(ev.timestamp).getUTCHours();
      const key = `${h < 10 ? '0' : ''}${h}:00`;
      hourlyActivity[key] = (hourlyActivity[key] || 0) + 1;
    }
  });
  const maxActivity = Math.max(...Object.values(hourlyActivity), 1);

  return (
    <>
      <Head>
        <title>BrowserMCP Intelligence Dashboard</title>
        <meta name="description" content="Unified observability and intelligence dashboard for BrowserMCP." />
      </Head>

      <style dangerouslySetInnerHTML={{ __html: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }

        body {
          background: #090d16;
          color: #f1f5f9;
          font-family: 'Inter', sans-serif;
          min-height: 100vh;
          overflow-x: hidden;
        }

        .dashboard-layout {
          max-width: 1380px;
          margin: 0 auto;
          padding: 24px 20px 60px;
        }

        .top-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 28px;
          padding-bottom: 18px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }

        .brand-title {
          font-size: 1.4rem;
          font-weight: 700;
          letter-spacing: -0.5px;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .brand-badge {
          background: linear-gradient(135deg, #0ea5e9, #3b82f6);
          color: white;
          font-size: 0.72rem;
          padding: 3px 8px;
          border-radius: 6px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .nav-links {
          display: flex;
          gap: 12px;
        }

        .nav-button {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #94a3b8;
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 0.88rem;
          text-decoration: none;
          font-weight: 500;
          transition: all 0.2s;
          cursor: pointer;
        }

        .nav-button:hover, .nav-button.active {
          background: rgba(56, 189, 248, 0.15);
          color: #38bdf8;
          border-color: rgba(56, 189, 248, 0.4);
        }

        /* Glassmorphism Card Style */
        .glass-card {
          background: rgba(15, 23, 42, 0.75);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
          padding: 22px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
          margin-bottom: 24px;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .card-title {
          font-size: 1.05rem;
          font-weight: 600;
          color: #e2e8f0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        /* Ask Bar Section */
        .ask-container {
          background: linear-gradient(145deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
          border: 1px solid rgba(56, 189, 248, 0.25);
          box-shadow: 0 0 35px rgba(56, 189, 248, 0.08);
        }

        .ask-input-box {
          display: flex;
          gap: 12px;
          margin-top: 14px;
        }

        .ask-input {
          flex: 1;
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 12px;
          padding: 16px 20px;
          color: #fff;
          font-size: 1.05rem;
          font-family: inherit;
          outline: none;
          transition: all 0.2s;
        }

        .ask-input:focus {
          border-color: #38bdf8;
          box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
        }

        .ask-btn {
          background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
          color: #fff;
          border: none;
          border-radius: 12px;
          padding: 0 28px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .ask-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
        }

        .ask-btn:disabled {
          background: #334155;
          color: #64748b;
          cursor: not-allowed;
        }

        .preset-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 14px;
        }

        .preset-chip {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.08);
          color: #94a3b8;
          padding: 5px 12px;
          border-radius: 20px;
          font-size: 0.82rem;
          cursor: pointer;
          transition: all 0.15s;
        }

        .preset-chip:hover {
          background: rgba(56, 189, 248, 0.15);
          color: #38bdf8;
          border-color: rgba(56, 189, 248, 0.3);
        }

        /* Ask Result Box */
        .result-box {
          margin-top: 20px;
          padding: 18px;
          background: rgba(15, 23, 42, 0.9);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          animation: fadeIn 0.3s ease-out;
        }

        .result-answer {
          font-size: 1.05rem;
          line-height: 1.6;
          color: #f1f5f9;
          white-space: pre-wrap;
        }

        /* Stats Grid */
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .stat-card {
          background: rgba(15, 23, 42, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.07);
          border-radius: 14px;
          padding: 18px;
          text-align: left;
        }

        .stat-label {
          font-size: 0.8rem;
          color: #94a3b8;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 6px;
        }

        .stat-value {
          font-size: 1.8rem;
          font-weight: 700;
          color: #f8fafc;
        }

        .stat-sub {
          font-size: 0.78rem;
          color: #38bdf8;
          margin-top: 4px;
        }

        /* 2-Column Section Layout */
        .columns-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
        }

        @media (max-width: 960px) {
          .columns-grid {
            grid-template-columns: 1fr;
          }
        }

        /* Activity Chart */
        .chart-bars {
          display: flex;
          align-items: flex-end;
          gap: 6px;
          height: 120px;
          padding-top: 10px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .bar-col {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          height: 100%;
          justify-content: flex-end;
        }

        .bar-fill {
          width: 100%;
          background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
          border-radius: 3px 3px 0 0;
          transition: height 0.3s ease;
        }

        .bar-label {
          font-size: 0.65rem;
          color: #64748b;
          margin-top: 6px;
        }

        /* Status Badge */
        .status-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 0.78rem;
          font-weight: 600;
        }

        .status-online {
          background: rgba(34, 197, 94, 0.15);
          color: #4ade80;
          border: 1px solid rgba(34, 197, 94, 0.3);
        }

        .status-offline {
          background: rgba(239, 68, 68, 0.15);
          color: #f87171;
          border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .status-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: currentColor;
        }

        /* Buttons & Actions */
        .action-btn {
          background: rgba(30, 41, 59, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.12);
          color: #e2e8f0;
          padding: 6px 14px;
          border-radius: 8px;
          font-size: 0.82rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .action-btn:hover:not(:disabled) {
          background: rgba(56, 189, 248, 0.2);
          border-color: #38bdf8;
          color: #38bdf8;
        }

        .action-btn.active {
          background: rgba(239, 68, 68, 0.2);
          border-color: rgba(239, 68, 68, 0.4);
          color: #f87171;
        }

        /* List Items */
        .item-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .list-item {
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 10px;
          padding: 12px 16px;
          transition: all 0.2s;
        }

        .list-item:hover {
          border-color: rgba(255, 255, 255, 0.12);
          background: rgba(30, 41, 59, 0.5);
        }

        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;
        }

        .item-title {
          font-size: 0.92rem;
          font-weight: 600;
          color: #f1f5f9;
        }

        .item-meta {
          font-size: 0.78rem;
          color: #94a3b8;
          font-family: 'JetBrains Mono', monospace;
        }

        .item-desc {
          font-size: 0.84rem;
          color: #cbd5e1;
          line-height: 1.4;
        }

        /* Tool Grid */
        .tools-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
          gap: 10px;
        }

        .tool-card {
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 10px;
          padding: 12px;
        }

        .tool-name {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.86rem;
          font-weight: 600;
          color: #38bdf8;
          margin-bottom: 4px;
        }

        .tool-desc {
          font-size: 0.78rem;
          color: #94a3b8;
          line-height: 1.3;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}} />

      <div className="dashboard-layout">
        {/* Navigation / Header */}
        <div className="top-nav">
          <div className="brand-title">
            <span>⚡ BrowserMCP</span>
            <span className="brand-badge">Intelligence</span>
          </div>
          <div className="nav-links">
            <a href="/chat" className="nav-button">💬 Chat View</a>
            <a href="/dashboard" className="nav-button active">📊 Dashboard</a>
            <a href="/" className="nav-button">📜 Raw Timeline</a>
          </div>
        </div>

        {/* 1. ASK YOUR BROWSER */}
        <div className="glass-card ask-container">
          <div className="card-header">
            <div className="card-title">
              <span>🧠 Ask Your Browser</span>
            </div>
            <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Powered by Investigation Engine & MCP</span>
          </div>

          <p style={{ fontSize: "0.9rem", color: "#94a3b8" }}>
            Ask arbitrary natural-language questions grounded directly in your captured browser events with zero hallucination.
          </p>

          <form onSubmit={(e) => handleAskSubmit(e)}>
            <div className="ask-input-box">
              <input
                type="text"
                className="ask-input"
                placeholder="Ask anything about your browsing (e.g., What did I search on Stack Overflow?)..."
                value={askQuery}
                onChange={(e) => setAskQuery(e.target.value)}
                disabled={isAsking}
              />
              <button type="submit" className="ask-btn" disabled={isAsking || !askQuery.trim()}>
                {isAsking ? "Investigating..." : "Investigate"}
              </button>
            </div>
          </form>

          <div className="preset-chips">
            <span style={{ fontSize: "0.78rem", color: "#64748b", alignSelf: "center" }}>Quick questions:</span>
            <button className="preset-chip" onClick={() => handleAskSubmit(undefined, "What is my favourite programming language?")}>
              ⭐ Favourite programming language?
            </button>
            <button className="preset-chip" onClick={() => handleAskSubmit(undefined, "What did I search on Stack Overflow?")}>
              🔍 Searched on Stack Overflow?
            </button>
            <button className="preset-chip" onClick={() => handleAskSubmit(undefined, "What are my most visited websites?")}>
              🌐 Most visited websites?
            </button>
            <button className="preset-chip" onClick={() => handleAskSubmit(undefined, "Why does Java appear to be my favourite?")}>
              ☕ Why Java?
            </button>
          </div>

          {askError && (
            <div className="result-box" style={{ borderColor: "rgba(239, 68, 68, 0.4)", color: "#fca5a5" }}>
              ⚠️ {askError}
            </div>
          )}

          {askResult && (
            <div className="result-box">
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#38bdf8" }}>Evidence-Backed Conclusion:</span>
                <span style={{ fontSize: "0.78rem", color: "#94a3b8" }}>{askResult.evidence?.length || 0} source records</span>
              </div>
              <div className="result-answer">{askResult.answer}</div>

              {askResult.evidence && askResult.evidence.length > 0 && (
                <div style={{ marginTop: "14px" }}>
                  <button
                    className="action-btn"
                    onClick={() => setExpandedEvidence(!expandedEvidence)}
                  >
                    {expandedEvidence ? "Hide Evidence ▲" : `View Supporting Evidence (${askResult.evidence.length}) ▼`}
                  </button>

                  {expandedEvidence && (
                    <div style={{ marginTop: "10px", display: "flex", flexDirection: "column", gap: "6px" }}>
                      {askResult.evidence.slice(0, 10).map((ev) => (
                        <div key={ev.event_id} style={{ background: "rgba(0,0,0,0.3)", padding: "8px 12px", borderRadius: "6px", fontSize: "0.8rem" }}>
                          <div style={{ fontWeight: 600, color: "#e2e8f0" }}>{ev.title || "Untitled"}</div>
                          <div style={{ color: "#94a3b8" }}>{ev.snippet}</div>
                          {ev.url && <a href={ev.url} target="_blank" rel="noreferrer" style={{ color: "#38bdf8", fontSize: "0.74rem" }}>{ev.url}</a>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 2. SYSTEM OVERVIEW */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Events</div>
            <div className="stat-value">{stats.totalEvents}</div>
            <div className="stat-sub">Captured Browser Activity</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Unique Domains</div>
            <div className="stat-value">{stats.uniqueDomains}</div>
            <div className="stat-sub">Sites & Web Apps</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Searches / Inputs</div>
            <div className="stat-value">{stats.searchCount}</div>
            <div className="stat-sub">Captured Queries</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Browser Sessions</div>
            <div className="stat-value">{stats.sessionsCount}</div>
            <div className="stat-sub">Segmented Clusters</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">MCP Protocol</div>
            <div className="stat-value" style={{ fontSize: "1.3rem", color: mcpInfo ? "#4ade80" : "#f87171" }}>
              {mcpInfo ? "ONLINE" : "OFFLINE"}
            </div>
            <div className="stat-sub">{mcpTools.length} Composable Tools</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Continuous Watcher</div>
            <div className="stat-value" style={{ fontSize: "1.3rem", color: watcherStatus?.is_running ? "#4ade80" : "#94a3b8" }}>
              {watcherStatus?.is_running ? "ACTIVE" : "STOPPED"}
            </div>
            <div className="stat-sub">{watcherStatus?.total_alerts_triggered || 0} Alerts Triggered</div>
          </div>
        </div>

        {/* 3. ACTIVITY CHART */}
        <div className="glass-card">
          <div className="card-header">
            <div className="card-title">
              <span>📈 Activity Distribution (UTC Hours)</span>
            </div>
            <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Based on recent browser events</span>
          </div>

          <div className="chart-bars">
            {Object.entries(hourlyActivity).map(([hour, count]) => {
              const heightPct = Math.max((count / maxActivity) * 100, count > 0 ? 12 : 3);
              return (
                <div key={hour} className="bar-col" title={`${hour}: ${count} events`}>
                  <div
                    className="bar-fill"
                    style={{
                      height: `${heightPct}%`,
                      opacity: count > 0 ? 1 : 0.2,
                    }}
                  />
                  <div className="bar-label">{hour.slice(0, 2)}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 4 & 5. AI INSIGHTS & CONTINUOUS WATCHER */}
        <div className="columns-grid">
          {/* AI Insights (Self-Discovery) */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <span>✨ AI Insights & Self-Discovery</span>
              </div>
              <button
                className="action-btn"
                onClick={handleTriggerDiscovery}
                disabled={isRunningDiscovery}
              >
                {isRunningDiscovery ? "Discovering..." : "⚡ Run Discovery"}
              </button>
            </div>

            <p style={{ fontSize: "0.82rem", color: "#94a3b8", marginBottom: "14px" }}>
              Autonomous hypothesis generation across behavioral patterns, interests, and workflow habits.
            </p>

            {discoveries.length === 0 ? (
              <div style={{ textAlign: "center", padding: "24px 0", color: "#64748b", fontSize: "0.88rem" }}>
                No discoveries recorded yet. Click <strong>Run Discovery</strong> to analyze browser data.
              </div>
            ) : (
              <div className="item-list">
                {discoveries.slice(0, 4).map((disc) => (
                  <div key={disc.id} className="list-item">
                    <div className="item-header">
                      <span className="item-title">{disc.hypothesis}</span>
                      <span
                        className="status-pill"
                        style={{
                          background: disc.confidence === "CONFIRMED" ? "rgba(34, 197, 94, 0.15)" : "rgba(56, 189, 248, 0.15)",
                          color: disc.confidence === "CONFIRMED" ? "#4ade80" : "#38bdf8",
                        }}
                      >
                        {disc.confidence}
                      </span>
                    </div>
                    <div className="item-desc">{disc.narrative}</div>
                    {disc.supporting_evidence && disc.supporting_evidence.length > 0 && (
                      <div style={{ marginTop: "8px" }}>
                        <button
                          className="action-btn"
                          style={{ fontSize: "0.74rem", padding: "3px 8px" }}
                          onClick={() => setSelectedDiscovery(selectedDiscovery?.id === disc.id ? null : disc)}
                        >
                          {selectedDiscovery?.id === disc.id ? "Hide Evidence" : `View Evidence (${disc.supporting_evidence.length})`}
                        </button>

                        {selectedDiscovery?.id === disc.id && (
                          <div style={{ marginTop: "8px", background: "rgba(0,0,0,0.35)", padding: "8px", borderRadius: "6px" }}>
                            {disc.supporting_evidence.slice(0, 3).map((ev: any, idx: number) => (
                              <div key={idx} style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: "4px" }}>
                                • {ev.title || ev.domain || "Event"} {ev.input ? `(Query: '${ev.input}')` : ""}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Continuous Watcher */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <span>⏱️ Continuous Browser Watcher</span>
              </div>
              <button
                className={`action-btn ${watcherStatus?.is_running ? 'active' : ''}`}
                onClick={handleToggleWatcher}
                disabled={isTogglingWatcher}
              >
                {watcherStatus?.is_running ? "⏹ Stop Watcher" : "▶ Start Watcher"}
              </button>
            </div>

            <div style={{ display: "flex", gap: "12px", marginBottom: "14px" }}>
              <span className={`status-pill ${watcherStatus?.is_running ? 'status-online' : 'status-offline'}`}>
                <span className="status-dot"></span>
                {watcherStatus?.is_running ? "WATCHER ACTIVE" : "WATCHER STOPPED"}
              </span>
              <span style={{ fontSize: "0.82rem", color: "#94a3b8", alignSelf: "center" }}>
                {watcherStatus?.total_events_observed || 0} events observed
              </span>
            </div>

            <p style={{ fontSize: "0.82rem", color: "#94a3b8", marginBottom: "14px" }}>
              Monitors new events asynchronously, detects activity bursts, and flags interest changes without polling heavy LLMs.
            </p>

            <div className="item-list">
              {watcherAlerts.length === 0 ? (
                <div style={{ textAlign: "center", padding: "24px 0", color: "#64748b", fontSize: "0.88rem" }}>
                  {watcherStatus?.is_running ? "Watching stream... no shifts detected yet." : "Watcher is currently stopped."}
                </div>
              ) : (
                watcherAlerts.map((alert) => (
                  <div key={alert.id} className="list-item">
                    <div className="item-header">
                      <span className="item-title">{alert.title}</span>
                      <span className="item-meta">{alert.alert_type}</span>
                    </div>
                    <div className="item-desc">{alert.summary}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* 6 & 7. MCP SERVER & RECENT INVESTIGATIONS */}
        <div className="columns-grid">
          {/* MCP Server */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <span>🔌 Model Context Protocol (MCP)</span>
              </div>
              <button
                className="action-btn"
                onClick={handleTestMcp}
                disabled={isTestingMcp}
              >
                {isTestingMcp ? "Testing..." : "⚡ Test Tool"}
              </button>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
              <span className={`status-pill ${mcpInfo ? 'status-online' : 'status-offline'}`}>
                <span className="status-dot"></span>
                {mcpInfo ? "MCP PROTOCOL ACTIVE" : "MCP OFFLINE"}
              </span>
              <span style={{ fontSize: "0.82rem", color: "#94a3b8" }}>
                v{mcpInfo?.version || "1.0.0"} ({mcpTools.length} tools registered)
              </span>
            </div>

            {mcpTestResult && (
              <div style={{ background: "rgba(56, 189, 248, 0.1)", border: "1px solid rgba(56, 189, 248, 0.3)", padding: "10px 14px", borderRadius: "8px", fontSize: "0.82rem", color: "#7dd3fc", marginBottom: "14px" }}>
                {mcpTestResult}
              </div>
            )}

            <div className="tools-grid">
              {mcpTools.map((tool) => (
                <div key={tool.name} className="tool-card">
                  <div className="tool-name">{tool.name}</div>
                  <div className="tool-desc">{tool.description?.slice(0, 95)}...</div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Investigations */}
          <div className="glass-card">
            <div className="card-header">
              <div className="card-title">
                <span>📜 Recent Investigations</span>
              </div>
              <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Audit trail</span>
            </div>

            <p style={{ fontSize: "0.82rem", color: "#94a3b8", marginBottom: "14px" }}>
              Log of recent agentic query investigations executed through Ask or MCP tools.
            </p>

            {recentInvs.length === 0 ? (
              <div style={{ textAlign: "center", padding: "24px 0", color: "#64748b", fontSize: "0.88rem" }}>
                No recent investigations logged.
              </div>
            ) : (
              <div className="item-list">
                {recentInvs.slice(0, 5).map((inv) => (
                  <div key={inv.id} className="list-item">
                    <div className="item-header">
                      <span className="item-title" style={{ color: "#38bdf8" }}>&ldquo;{inv.query}&rdquo;</span>
                      <span className="item-meta">{inv.status}</span>
                    </div>
                    <div className="item-desc" style={{ fontSize: "0.8rem" }}>
                      {inv.summary ? inv.summary.slice(0, 140) + "..." : "Completed with evidence."}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </>
  );
}
