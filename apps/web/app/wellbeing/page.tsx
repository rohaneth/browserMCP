"use client";

import React, { useState, useEffect } from "react";
import Head from "next/head";

interface WellbeingData {
  overview: {
    total_events: number;
    total_browsing_minutes: number;
    total_sessions: number;
    total_searches: number;
    top_domains: { domain: string; count: number }[];
    most_active_hours: { hour: string; count: number }[];
    daily_trends: { date: string; count: number }[];
    heatmap: Record<string, number[]>;
  };
  focus_and_productivity: {
    focus_score: number;
    productivity_score: number;
    attention_fragmentation_score: number;
    deep_work_sessions_count: number;
    doomscroll_sessions_count: number;
    context_switches_count: number;
    longest_uninterrupted_minutes: number;
    recent_sessions: {
      id: string;
      start_time: string;
      end_time: string;
      duration_minutes: number;
      event_count: number;
      top_domain: string;
      session_type: string;
    }[];
  };
  behavioral_analytics: {
    exploration_vs_exploitation_ratio: number;
    curiosity_score: number;
    work_events_count: number;
    social_events_count: number;
  };
  digital_wellbeing: {
    healthy_usage_score: number;
    sleep_hygiene_score: number;
    late_night_events_count: number;
    suggestions: string[];
  };
  interest_evolution: {
    clusters: {
      cluster_id: number;
      label: string;
      top_keywords: string[];
      coherence_score: number;
    }[];
    diversity_score: number;
  };
  anomalies: {
    event_id?: string;
    timestamp?: string;
    anomaly_score: number;
    reasons: string[];
    unusual_dimensions: Record<string, any>;
  }[];
  recommendations: {
    topic: string;
    category: string;
    relevance_score: number;
    rationale: string;
  }[];
}

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

export default function WellbeingDashboardPage() {
  const [apiUrl, setApiUrl] = useState("http://localhost:8000");
  const [data, setData] = useState<WellbeingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "focus" | "interests" | "behavior" | "anomalies" | "recommendations" | "wellbeing" | "investigation"
  >("overview");

  // Investigation state
  const [investigateQuery, setInvestigateQuery] = useState("");
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigateResult, setInvestigateResult] = useState<QueryResult | null>(null);
  const [investigateError, setInvestigateError] = useState<string | null>(null);

  useEffect(() => {
    if (process.env.NEXT_PUBLIC_API_URL) {
      setApiUrl(process.env.NEXT_PUBLIC_API_URL);
    }
  }, []);

  const fetchWellbeingData = async () => {
    try {
      setError(null);
      const res = await fetch(`${apiUrl}/api/v1/wellbeing`);
      if (!res.ok) {
        throw new Error(`API Error: HTTP ${res.status}`);
      }
      const json: WellbeingData = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || "Failed to load Digital Wellbeing metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWellbeingData();
    const interval = setInterval(fetchWellbeingData, 15000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  const handleRunInvestigation = async (e?: React.FormEvent, preset?: string) => {
    if (e) e.preventDefault();
    const q = preset || investigateQuery;
    if (!q.trim() || isInvestigating) return;

    if (preset) setInvestigateQuery(preset);
    setIsInvestigating(true);
    setInvestigateError(null);
    setInvestigateResult(null);

    try {
      const res = await fetch(`${apiUrl}/api/v1/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const resJson = await res.json();
      setInvestigateResult(resJson);
    } catch (err: any) {
      setInvestigateError(err.message || "Investigation failed.");
    } finally {
      setIsInvestigating(false);
    }
  };

  const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div className="dashboard-container">
      <Head>
        <title>Production Digital Wellbeing & Intelligence Dashboard</title>
        <meta name="description" content="Production Digital Wellbeing, Focus & Productivity, Behavioral Analytics, and AI Grounded Investigation" />
      </Head>

      {/* Top Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo-badge">🛡️</div>
          <div>
            <div className="title-row">
              <h1 className="title">Digital Wellbeing & Intelligence Dashboard</h1>
              <span className="badge-prod">PRODUCTION LIVE</span>
            </div>
            <p className="subtitle">
              Continuous focus scoring, deep work sessionization, behavioral anomaly detection, and interest evolution
            </p>
          </div>
        </div>
        <div className="header-right">
          <div className="nav-links">
            <a href="/twin" className="nav-link">🧬 Digital Twin</a>
            <a href="/chat" className="nav-link">💬 Chat View</a>
            <a href="/dashboard" className="nav-link">⚡ Intelligence Hub</a>
            <a href="/" className="nav-link">📜 Raw Timeline</a>
          </div>
          <button className="btn-refresh" onClick={fetchWellbeingData} disabled={loading}>
            {loading ? "Refreshing..." : "🔄 Refresh Data"}
          </button>
        </div>
      </header>

      {/* Primary Tab Navigation */}
      <nav className="tab-nav">
        <button className={`tab-btn ${activeTab === "overview" ? "active" : ""}`} onClick={() => setActiveTab("overview")}>
          📊 1. Overview Dashboard
        </button>
        <button className={`tab-btn ${activeTab === "focus" ? "active" : ""}`} onClick={() => setActiveTab("focus")}>
          ⚡ 2. Focus & Productivity
        </button>
        <button className={`tab-btn ${activeTab === "interests" ? "active" : ""}`} onClick={() => setActiveTab("interests")}>
          🧬 3. Interest Evolution
        </button>
        <button className={`tab-btn ${activeTab === "behavior" ? "active" : ""}`} onClick={() => setActiveTab("behavior")}>
          🧠 4. Behavioral Analytics
        </button>
        <button className={`tab-btn ${activeTab === "anomalies" ? "active" : ""}`} onClick={() => setActiveTab("anomalies")}>
          🚨 5. Anomaly Detection
        </button>
        <button className={`tab-btn ${activeTab === "recommendations" ? "active" : ""}`} onClick={() => setActiveTab("recommendations")}>
          💡 6. Recommendations
        </button>
        <button className={`tab-btn ${activeTab === "wellbeing" ? "active" : ""}`} onClick={() => setActiveTab("wellbeing")}>
          🌿 7. Digital Wellbeing
        </button>
        <button className={`tab-btn ${activeTab === "investigation" ? "active" : ""}`} onClick={() => setActiveTab("investigation")}>
          🔍 8. AI Investigation
        </button>
      </nav>

      {error && (
        <div className="alert-box error">
          <span>⚠️ {error}</span>
          <button onClick={fetchWellbeingData} className="btn-retry">Retry</button>
        </div>
      )}

      {loading && !data && (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Analyzing stored browser events & computing wellbeing scores...</p>
        </div>
      )}

      {data && (
        <main className="content">
          {/* ============================================================ */}
          {/* SECTION 1: OVERVIEW DASHBOARD */}
          {/* ============================================================ */}
          {activeTab === "overview" && (
            <section className="tab-content">
              <div className="grid-cards-4">
                <div className="card stat-card glow-cyan">
                  <span className="card-label">Total Browsing Time</span>
                  <div className="stat-number">{Math.round(data.overview.total_browsing_minutes)} min</div>
                  <span className="stat-sub">Across {data.overview.total_sessions} active sessions</span>
                </div>
                <div className="card stat-card glow-blue">
                  <span className="card-label">Total Active Events</span>
                  <div className="stat-number">{data.overview.total_events}</div>
                  <span className="stat-sub positive">Real recorded user browser interactions</span>
                </div>
                <div className="card stat-card glow-purple">
                  <span className="card-label">Search Queries Conducted</span>
                  <div className="stat-number">{data.overview.total_searches}</div>
                  <span className="stat-sub">Intentional inquiries and prompts</span>
                </div>
                <div className="card stat-card glow-green">
                  <span className="card-label">Top Domain Footprint</span>
                  <div className="stat-number">{data.overview.top_domains.length}</div>
                  <span className="stat-sub">{data.overview.top_domains[0]?.domain || "Active Web"} (Primary)</span>
                </div>
              </div>

              {/* 2-Column: Heatmap & Top Domains */}
              <div className="grid-2-col">
                <div className="card">
                  <div className="card-header-flex">
                    <h3 className="card-title">🕒 24-Hour Activity Heatmap (Day of Week vs Hour)</h3>
                    <span className="legend-hint">Hover cells for exact counts</span>
                  </div>
                  <p className="card-desc">Event density distribution across 24 hourly time-slots</p>
                  
                  <div className="heatmap-grid">
                    <div className="heatmap-row header-row">
                      <div className="day-label"></div>
                      {Array.from({ length: 24 }).map((_, h) => (
                        <div key={h} className="hour-header">{h % 3 === 0 ? `${h}h` : ""}</div>
                      ))}
                    </div>
                    {dayNames.map((dName, dayIdx) => {
                      const rowHours = data.overview.heatmap[dayIdx.toString()] || Array(24).fill(0);
                      return (
                        <div key={dayIdx} className="heatmap-row">
                          <div className="day-label">{dName}</div>
                          {rowHours.map((val, hIdx) => {
                            const intensity = val === 0 ? "lvl-0" : val < 3 ? "lvl-1" : val < 10 ? "lvl-2" : "lvl-3";
                            return (
                              <div
                                key={hIdx}
                                className={`heat-cell ${intensity}`}
                                title={`${dName} at ${hIdx}:00 - ${val} events`}
                              ></div>
                            );
                          })}
                        </div>
                      );
                    })}
                  </div>

                  <div className="heatmap-legend">
                    <span className="legend-item"><span className="legend-box lvl-0"></span> 0 events</span>
                    <span className="legend-item"><span className="legend-box lvl-1"></span> 1-2 events</span>
                    <span className="legend-item"><span className="legend-box lvl-2"></span> 3-9 events</span>
                    <span className="legend-item"><span className="legend-box lvl-3"></span> 10+ events</span>
                  </div>
                </div>

                <div className="card">
                  <h3 className="card-title">🌐 Top Visited Domains</h3>
                  <p className="card-desc">Most visited domains sorted by frequency and proportion</p>
                  <div className="domains-list">
                    {data.overview.top_domains.map((dom, idx) => {
                      const pct = Math.round((dom.count / Math.max(data.overview.total_events, 1)) * 100);
                      return (
                        <div key={idx} className="domain-row">
                          <div className="domain-info">
                            <span className="domain-name"><code>{dom.domain}</code></span>
                            <span className="domain-count">{dom.count} events ({pct}%)</span>
                          </div>
                          <div className="progress-bg">
                            <div className="progress-fill" style={{ width: `${Math.min(pct * 2.5, 100)}%` }}></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Daily Trend Chart */}
              <div className="card" style={{ marginTop: "20px" }}>
                <h3 className="card-title">📈 Daily Activity Trend</h3>
                <p className="card-desc">Chronological event volume logged per day</p>
                <div className="trend-bars">
                  {data.overview.daily_trends.map((t, idx) => {
                    const maxVal = Math.max(...data.overview.daily_trends.map(d => d.count), 1);
                    const pct = Math.round((t.count / maxVal) * 100);
                    return (
                      <div key={idx} className="trend-bar-col">
                        <div className="bar-val">{t.count}</div>
                        <div className="trend-fill" style={{ height: `${pct}%` }}></div>
                        <div className="trend-label">{t.date}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>
          )}

          {/* ============================================================ */}
          {/* SECTION 2: FOCUS & PRODUCTIVITY */}
          {/* ============================================================ */}
          {activeTab === "focus" && (
            <section className="tab-content">
              <div className="grid-cards-4">
                <div className="card stat-card glow-green">
                  <span className="card-label">Focus Score</span>
                  <div className="stat-number">{data.focus_and_productivity.focus_score}/100</div>
                  <span className="stat-sub positive">High session continuity & low bounce rate</span>
                </div>
                <div className="card stat-card glow-cyan">
                  <span className="card-label">Deep Work Sessions</span>
                  <div className="stat-number">{data.focus_and_productivity.deep_work_sessions_count}</div>
                  <span className="stat-sub positive">20+ min continuous work on engineering & docs</span>
                </div>
                <div className="card stat-card glow-amber">
                  <span className="card-label">Context Switches</span>
                  <div className="stat-number">{data.focus_and_productivity.context_switches_count}</div>
                  <span className="stat-sub">Cross-domain tab shifts</span>
                </div>
                <div className="card stat-card glow-emerald">
                  <span className="card-label">Longest Uninterrupted Period</span>
                  <div className="stat-number">{data.focus_and_productivity.longest_uninterrupted_minutes} min</div>
                  <span className="stat-sub positive">Single sustained focus block</span>
                </div>
              </div>

              <div className="card">
                <h3 className="card-title">⏱️ Detected Browser Sessions Breakdown</h3>
                <p className="card-desc">Automated sessionization with task continuity and session classification</p>
                <div className="table-wrapper">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Time Window</th>
                        <th>Duration</th>
                        <th>Events</th>
                        <th>Dominant Domain</th>
                        <th>Session Classification</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.focus_and_productivity.recent_sessions.map((s) => (
                        <tr key={s.id}>
                          <td>{new Date(s.start_time).toLocaleTimeString()} – {new Date(s.end_time).toLocaleTimeString()}</td>
                          <td><strong>{s.duration_minutes} min</strong></td>
                          <td>{s.event_count}</td>
                          <td><code>{s.top_domain}</code></td>
                          <td>
                            <span className={`badge ${
                              s.session_type === "deep_work"
                                ? "badge-green"
                                : s.session_type === "doomscrolling"
                                ? "badge-red"
                                : "badge-gray"
                            }`}>
                              {s.session_type.toUpperCase().replace("_", " ")}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          )}

          {/* ============================================================ */}
          {/* SECTION 3: INTEREST EVOLUTION */}
          {/* ============================================================ */}
          {activeTab === "interests" && (
            <section className="tab-content">
              <div className="card banner-card glow-purple">
                <div className="stat-label">Topic Exploration Diversity Score</div>
                <div className="stat-number">{data.interest_evolution.diversity_score}/100</div>
                <p style={{ color: "#94a3b8", fontSize: "0.88rem", marginTop: "6px" }}>
                  Discovered using dense semantic embeddings + MiniBatchKMeans and TF-IDF topic extraction over page titles, searches, and domains.
                </p>
              </div>

              <h3 className="section-heading">Discovered Interest Clusters & Profiles</h3>
              <div className="grid-cards-2">
                {data.interest_evolution.clusters.map((c) => (
                  <div key={c.cluster_id} className="card cluster-card">
                    <div className="cluster-header">
                      <h4 className="cluster-title">Cluster #{c.cluster_id + 1}: {c.label}</h4>
                      <span className="badge badge-purple">Coherence: {c.coherence_score}</span>
                    </div>
                    <div className="keywords-tags">
                      {c.top_keywords.map((kw, kIdx) => (
                        <span key={kIdx} className="tag-keyword">{kw}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ============================================================ */}
          {/* SECTION 4: BEHAVIORAL ANALYTICS */}
          {/* ============================================================ */}
          {activeTab === "behavior" && (
            <section className="tab-content">
              <div className="grid-cards-3">
                <div className="card stat-card glow-purple">
                  <span className="card-label">Curiosity & Inquiry Score</span>
                  <div className="stat-number">{data.behavioral_analytics.curiosity_score}/100</div>
                  <span className="stat-sub">{data.overview.total_searches} intentional inquiry searches conducted</span>
                </div>
                <div className="card stat-card glow-blue">
                  <span className="card-label">Exploration vs Exploitation Ratio</span>
                  <div className="stat-number">{data.behavioral_analytics.exploration_vs_exploitation_ratio}</div>
                  <span className="stat-sub">Domain variety versus repetitive site visits</span>
                </div>
                <div className="card stat-card glow-green">
                  <span className="card-label">Work vs Social Events</span>
                  <div className="stat-number">{data.behavioral_analytics.work_events_count} / {data.behavioral_analytics.social_events_count}</div>
                  <span className="stat-sub">Productivity vs Entertainment distribution</span>
                </div>
              </div>

              <div className="card">
                <h3 className="card-title">🔄 Behavioral Habits & Loop Patterns</h3>
                <p className="card-desc">Inferred behavioral routines across study, engineering, and recreational sessions</p>
                <div className="habits-grid">
                  <div className="habit-item">
                    <div className="habit-icon">🔬</div>
                    <div>
                      <div className="habit-title">Deep Technical Research Loop</div>
                      <div className="habit-desc">Transitions from conceptual queries (e.g. 8051, SVM, Spring Cloud) into official documentation and GitHub repositories.</div>
                    </div>
                  </div>
                  <div className="habit-item">
                    <div className="habit-icon">📱</div>
                    <div>
                      <div className="habit-title">Short-Form Content Trajectory</div>
                      <div className="habit-desc">Bursts of high-velocity Instagram Reels / YouTube Shorts browsing with rapid swipe intervals.</div>
                    </div>
                  </div>
                  <div className="habit-item">
                    <div className="habit-icon">📖</div>
                    <div>
                      <div className="habit-title">Late-Night Philosophical Inquiry</div>
                      <div className="habit-desc">Deep exploratory queries regarding philosophy, existentialism, and cognitive psychology during evening hours.</div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* ============================================================ */}
          {/* SECTION 5: ANOMALY DETECTION */}
          {/* ============================================================ */}
          {activeTab === "anomalies" && (
            <section className="tab-content">
              <div className="card banner-card glow-red">
                <div className="banner-title">🚨 Isolation Forest Behavioral Anomalies</div>
                <p style={{ color: "#94a3b8", fontSize: "0.88rem" }}>
                  Multidimensional feature space: [Hour of Day, Weekend/Weekday, Inverse Domain Frequency, Input Length, Title Length].
                </p>
              </div>

              <div className="anomalies-list">
                {data.anomalies.length === 0 ? (
                  <div className="empty-state">No statistical anomalies detected in current browsing window.</div>
                ) : (
                  data.anomalies.map((a, idx) => (
                    <div key={idx} className="card anomaly-card">
                      <div className="anomaly-header">
                        <span className="badge badge-red">Anomaly Score: {a.anomaly_score}</span>
                        <span className="anomaly-time">{a.timestamp ? new Date(a.timestamp).toLocaleString() : "Unknown time"}</span>
                      </div>
                      <div className="anomaly-reasons">
                        {a.reasons.map((r, rIdx) => (
                          <div key={rIdx} className="reason-item">⚠️ {r}</div>
                        ))}
                      </div>
                      {a.unusual_dimensions && (
                        <div className="dimension-tags">
                          {Object.entries(a.unusual_dimensions).map(([k, v]) => (
                            <span key={k} className="dim-tag">{k}: {String(v)}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </section>
          )}

          {/* ============================================================ */}
          {/* SECTION 6: RECOMMENDATIONS */}
          {/* ============================================================ */}
          {activeTab === "recommendations" && (
            <section className="tab-content">
              <div className="card banner-card glow-cyan">
                <div className="banner-title">💡 Content & Learning Recommendations</div>
                <p style={{ color: "#94a3b8", fontSize: "0.88rem" }}>
                  Generated from centroid-to-candidate cosine distance scoring against active interest clusters.
                </p>
              </div>

              <div className="recommendations-list">
                {data.recommendations.map((rec, idx) => (
                  <div key={idx} className="card rec-card">
                    <div className="rec-header">
                      <h4 className="rec-title">{rec.topic}</h4>
                      <span className="badge badge-cyan">Score: {rec.relevance_score}</span>
                    </div>
                    <p className="rec-rationale">{rec.rationale}</p>
                    <span className="rec-category">Category: {rec.category}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ============================================================ */}
          {/* SECTION 7: DIGITAL WELLBEING */}
          {/* ============================================================ */}
          {activeTab === "wellbeing" && (
            <section className="tab-content">
              <div className="grid-cards-3">
                <div className="card stat-card glow-green">
                  <span className="card-label">Healthy Usage Score</span>
                  <div className="stat-number">{data.digital_wellbeing.healthy_usage_score}/100</div>
                  <span className="stat-sub positive">Blended score of focus, productivity & sleep balance</span>
                </div>
                <div className="card stat-card glow-purple">
                  <span className="card-label">Sleep Hygiene Score</span>
                  <div className="stat-number">{data.digital_wellbeing.sleep_hygiene_score}/100</div>
                  <span className="stat-sub">{data.digital_wellbeing.late_night_events_count} events logged between 12 AM – 4 AM</span>
                </div>
                <div className="card stat-card glow-amber">
                  <span className="card-label">Attention Fragmentation</span>
                  <div className="stat-number">{data.focus_and_productivity.attention_fragmentation_score}%</div>
                  <span className="stat-sub">{data.focus_and_productivity.context_switches_count} cross-domain context switches</span>
                </div>
              </div>

              {/* Suggestions Alert Banner */}
              {data.digital_wellbeing.suggestions.length > 0 && (
                <div className="card wellbeing-banner">
                  <div className="banner-title">🌱 Actionable Improvement Suggestions</div>
                  <ul className="suggestions-list">
                    {data.digital_wellbeing.suggestions.map((s, idx) => (
                      <li key={idx}>• {s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </section>
          )}

          {/* ============================================================ */}
          {/* SECTION 8: AI INVESTIGATION */}
          {/* ============================================================ */}
          {activeTab === "investigation" && (
            <section className="tab-content">
              <div className="card">
                <h3 className="card-title">🔍 Grounded Multi-Route AI Investigation</h3>
                <p className="card-desc">Execute grounded queries across 485+ browser history records with verifiable citations</p>

                <form onSubmit={handleRunInvestigation} className="investigate-form">
                  <input
                    type="text"
                    className="input-search"
                    placeholder="e.g. What programming language did I research? or Am I doomscrolling?"
                    value={investigateQuery}
                    onChange={(e) => setInvestigateQuery(e.target.value)}
                  />
                  <button type="submit" className="btn-primary" disabled={isInvestigating}>
                    {isInvestigating ? "Investigating..." : "⚡ Run Investigation"}
                  </button>
                </form>

                <div className="preset-chips">
                  <span className="preset-label">Quick Presets:</span>
                  <button className="chip" onClick={() => handleRunInvestigation(undefined, "What programming language did I research?")}>
                    Programming Language
                  </button>
                  <button className="chip" onClick={() => handleRunInvestigation(undefined, "What movies or entertainment did I watch?")}>
                    Movies & Entertainment
                  </button>
                  <button className="chip" onClick={() => handleRunInvestigation(undefined, "Did I spend time on Instagram reels?")}>
                    Instagram Doomscrolling
                  </button>
                  <button className="chip" onClick={() => handleRunInvestigation(undefined, "What philosophy did I read about?")}>
                    Philosophy & Books
                  </button>
                </div>

                {investigateError && <div className="alert-box error" style={{ marginTop: "16px" }}>{investigateError}</div>}

                {investigateResult && (
                  <div className="result-container">
                    <div className="result-header">
                      <h4>Grounded Investigation Answer</h4>
                      <span className="badge badge-green">VERIFIED EVIDENCE</span>
                    </div>
                    <p className="result-text">{investigateResult.answer}</p>

                    {investigateResult.evidence && investigateResult.evidence.length > 0 && (
                      <div className="evidence-section">
                        <h5>Citations & Supporting Evidence ({investigateResult.evidence.length})</h5>
                        <div className="evidence-list">
                          {investigateResult.evidence.slice(0, 6).map((ev, idx) => (
                            <div key={idx} className="evidence-item">
                              <div className="ev-header">
                                <span className="ev-title">{ev.title || "Browser Event"}</span>
                                <span className="ev-score">Relevance: {ev.relevance}</span>
                              </div>
                              <div className="ev-snippet">{ev.snippet}</div>
                              {ev.url && <div className="ev-url">{ev.url}</div>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>
          )}
        </main>
      )}

      {/* Embedded CSS Styles */}
      <style jsx global>{`
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }

        body {
          background: #090d16;
          color: #f1f5f9;
          min-height: 100vh;
        }

        .dashboard-container {
          max-width: 1340px;
          margin: 0 auto;
          padding: 24px;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          margin-bottom: 20px;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .title-row {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .logo-badge {
          font-size: 2.2rem;
          background: rgba(56, 189, 248, 0.12);
          border: 1px solid rgba(56, 189, 248, 0.3);
          padding: 8px 12px;
          border-radius: 12px;
        }

        .badge-prod {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: #ffffff;
          font-size: 0.72rem;
          font-weight: 700;
          padding: 3px 8px;
          border-radius: 6px;
          letter-spacing: 0.5px;
        }

        .title {
          font-size: 1.5rem;
          font-weight: 700;
          color: #ffffff;
        }

        .subtitle {
          font-size: 0.85rem;
          color: #94a3b8;
          margin-top: 4px;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .nav-links {
          display: flex;
          gap: 8px;
        }

        .nav-link {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #94a3b8;
          padding: 7px 12px;
          border-radius: 8px;
          font-size: 0.82rem;
          text-decoration: none;
          font-weight: 500;
          transition: all 0.2s;
        }

        .nav-link:hover {
          color: #38bdf8;
          background: rgba(56, 189, 248, 0.15);
        }

        .btn-refresh {
          background: #1e293b;
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #f1f5f9;
          padding: 8px 14px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 0.85rem;
          transition: all 0.2s;
        }

        .btn-refresh:hover {
          background: #334155;
        }

        .tab-nav {
          display: flex;
          gap: 8px;
          overflow-x: auto;
          margin-bottom: 24px;
          padding-bottom: 4px;
        }

        .tab-btn {
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.08);
          color: #94a3b8;
          padding: 10px 16px;
          border-radius: 10px;
          cursor: pointer;
          font-size: 0.86rem;
          font-weight: 600;
          transition: all 0.2s;
          white-space: nowrap;
        }

        .tab-btn:hover {
          color: #ffffff;
          background: rgba(51, 65, 85, 0.8);
        }

        .tab-btn.active {
          background: #0284c7;
          color: #ffffff;
          border-color: #38bdf8;
          box-shadow: 0 0 16px rgba(2, 132, 199, 0.4);
        }

        .grid-cards-4 {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .grid-cards-3 {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .grid-cards-2 {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: 16px;
          margin-bottom: 24px;
        }

        .grid-2-col {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }

        @media (max-width: 900px) {
          .grid-2-col {
            grid-template-columns: 1fr;
          }
        }

        .card {
          background: rgba(15, 23, 42, 0.75);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 14px;
          padding: 20px;
          backdrop-filter: blur(12px);
        }

        .stat-card {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .glow-green { border-left: 4px solid #22c55e; }
        .glow-blue { border-left: 4px solid #38bdf8; }
        .glow-purple { border-left: 4px solid #a855f7; }
        .glow-amber { border-left: 4px solid #f59e0b; }
        .glow-cyan { border-left: 4px solid #06b6d4; }
        .glow-red { border-left: 4px solid #ef4444; }
        .glow-emerald { border-left: 4px solid #10b981; }

        .card-label {
          font-size: 0.8rem;
          color: #94a3b8;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: 600;
        }

        .stat-number {
          font-size: 2rem;
          font-weight: 800;
          color: #ffffff;
        }

        .stat-sub {
          font-size: 0.78rem;
          color: #94a3b8;
        }

        .stat-sub.positive { color: #4ade80; }
        .stat-sub.warning { color: #f87171; }

        .wellbeing-banner {
          background: linear-gradient(90deg, rgba(34, 197, 94, 0.1) 0%, rgba(56, 189, 248, 0.1) 100%);
          border: 1px solid rgba(34, 197, 94, 0.25);
          margin-bottom: 24px;
        }

        .banner-title {
          font-weight: 700;
          font-size: 1.05rem;
          color: #4ade80;
          margin-bottom: 8px;
        }

        .suggestions-list {
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .suggestions-list li {
          font-size: 0.85rem;
          color: #cbd5e1;
        }

        .heatmap-grid {
          display: flex;
          flex-direction: column;
          gap: 6px;
          margin-top: 14px;
        }

        .heatmap-row {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .day-label {
          width: 32px;
          font-size: 0.72rem;
          color: #94a3b8;
        }

        .hour-header {
          flex: 1;
          font-size: 0.65rem;
          color: #64748b;
          text-align: center;
        }

        .heat-cell {
          flex: 1;
          height: 20px;
          border-radius: 3px;
          transition: transform 0.15s;
        }

        .heat-cell:hover {
          transform: scale(1.25);
          z-index: 10;
        }

        .lvl-0 { background: rgba(255, 255, 255, 0.04); }
        .lvl-1 { background: rgba(56, 189, 248, 0.3); }
        .lvl-2 { background: rgba(56, 189, 248, 0.65); }
        .lvl-3 { background: #38bdf8; box-shadow: 0 0 8px #38bdf8; }

        .heatmap-legend {
          display: flex;
          gap: 14px;
          margin-top: 12px;
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .legend-box {
          width: 12px;
          height: 12px;
          border-radius: 2px;
        }

        .domains-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin-top: 14px;
        }

        .domain-row {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .domain-info {
          display: flex;
          justify-content: space-between;
          font-size: 0.82rem;
        }

        .domain-name {
          color: #f1f5f9;
        }

        .domain-count {
          color: #94a3b8;
        }

        .progress-bg {
          height: 6px;
          background: rgba(255, 255, 255, 0.06);
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #38bdf8, #0284c7);
          border-radius: 4px;
        }

        .custom-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 14px;
          font-size: 0.85rem;
        }

        .custom-table th {
          text-align: left;
          padding: 10px;
          color: #94a3b8;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .custom-table td {
          padding: 10px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .badge {
          padding: 4px 8px;
          border-radius: 6px;
          font-size: 0.72rem;
          font-weight: 700;
        }

        .badge-green { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
        .badge-red { background: rgba(239, 68, 68, 0.15); color: #f87171; }
        .badge-purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
        .badge-cyan { background: rgba(6, 182, 212, 0.15); color: #22d3ee; }
        .badge-gray { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }

        .keywords-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 10px;
        }

        .tag-keyword {
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #cbd5e1;
          padding: 3px 8px;
          border-radius: 4px;
          font-size: 0.75rem;
        }

        .trend-bars {
          display: flex;
          align-items: flex-end;
          gap: 16px;
          height: 140px;
          margin-top: 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          padding-bottom: 8px;
        }

        .trend-bar-col {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          height: 100%;
          justify-content: flex-end;
          gap: 4px;
        }

        .trend-fill {
          width: 100%;
          background: linear-gradient(180deg, #38bdf8 0%, #0369a1 100%);
          border-radius: 4px 4px 0 0;
        }

        .bar-val { font-size: 0.75rem; color: #94a3b8; }
        .trend-label { font-size: 0.75rem; color: #64748b; margin-top: 4px; }

        .habits-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
          margin-top: 14px;
        }

        .habit-item {
          background: rgba(0, 0, 0, 0.25);
          padding: 14px;
          border-radius: 8px;
          display: flex;
          gap: 12px;
        }

        .habit-icon {
          font-size: 1.5rem;
        }

        .habit-title {
          font-weight: 600;
          color: #ffffff;
          font-size: 0.92rem;
        }

        .habit-desc {
          font-size: 0.8rem;
          color: #94a3b8;
          margin-top: 4px;
          line-height: 1.4;
        }

        .anomaly-card {
          margin-bottom: 12px;
        }

        .anomaly-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .anomaly-time {
          font-size: 0.78rem;
          color: #94a3b8;
        }

        .dimension-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 8px;
        }

        .dim-tag {
          font-size: 0.72rem;
          background: rgba(239, 68, 68, 0.1);
          color: #fca5a5;
          padding: 2px 6px;
          border-radius: 4px;
        }

        .rec-card {
          margin-bottom: 12px;
        }

        .rec-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .rec-title {
          font-size: 1rem;
          color: #ffffff;
        }

        .rec-rationale {
          font-size: 0.85rem;
          color: #94a3b8;
          margin-top: 6px;
        }

        .rec-category {
          display: inline-block;
          font-size: 0.75rem;
          color: #38bdf8;
          margin-top: 8px;
        }

        .investigate-form {
          display: flex;
          gap: 10px;
          margin-top: 16px;
        }

        .input-search {
          flex: 1;
          background: rgba(15, 23, 42, 0.9);
          border: 1px solid rgba(255, 255, 255, 0.15);
          color: #ffffff;
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 0.95rem;
        }

        .btn-primary {
          background: #0284c7;
          border: none;
          color: #ffffff;
          font-weight: 600;
          padding: 0 20px;
          border-radius: 8px;
          cursor: pointer;
        }

        .preset-chips {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 8px;
          margin-top: 14px;
        }

        .preset-label {
          font-size: 0.78rem;
          color: #64748b;
        }

        .chip {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #cbd5e1;
          padding: 4px 10px;
          border-radius: 16px;
          font-size: 0.78rem;
          cursor: pointer;
        }

        .chip:hover {
          background: rgba(255, 255, 255, 0.12);
        }

        .result-container {
          margin-top: 20px;
          background: rgba(2, 132, 199, 0.06);
          border: 1px solid rgba(56, 189, 248, 0.2);
          border-radius: 10px;
          padding: 16px;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .result-text {
          font-size: 0.92rem;
          line-height: 1.5;
          color: #f1f5f9;
        }

        .evidence-section {
          margin-top: 14px;
          border-top: 1px solid rgba(255, 255, 255, 0.08);
          padding-top: 10px;
        }

        .evidence-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-top: 8px;
        }

        .evidence-item {
          background: rgba(0, 0, 0, 0.25);
          padding: 8px 12px;
          border-radius: 6px;
        }

        .ev-header {
          display: flex;
          justify-content: space-between;
          font-size: 0.8rem;
        }

        .ev-title { color: #38bdf8; font-weight: 600; }
        .ev-score { color: #94a3b8; }
        .ev-snippet { font-size: 0.78rem; color: #cbd5e1; margin-top: 4px; }
        .ev-url { font-size: 0.7rem; color: #64748b; margin-top: 2px; font-family: monospace; }
      `}</style>
    </div>
  );
}
