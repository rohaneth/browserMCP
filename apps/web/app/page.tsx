"use client";

import React, { useState, useEffect } from "react";

interface BrowserEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  url?: string;
  domain?: string;
  page_title?: string;
  content?: string;
  input_text?: string;
  source: string;
  metadata?: Record<string, any>;
}

interface TimelineResponse {
  events: BrowserEvent[];
  total_count: number;
  limit: number;
  offset: number;
}

export default function TimelinePage() {
  const [events, setEvents] = useState<BrowserEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [domainFilter, setDomainFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 1000;

  const fetchTimeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1/timeline` : 'http://localhost:8000/api/v1/timeline');
      if (domainFilter) url.searchParams.append("domain", domainFilter);
      if (typeFilter) url.searchParams.append("event_type", typeFilter);
      url.searchParams.append("limit", limit.toString());
      url.searchParams.append("offset", offset.toString());

      const res = await fetch(url.toString());
      if (!res.ok) {
        throw new Error(`API Error: ${res.status} ${res.statusText}`);
      }
      const data: TimelineResponse = await res.json();
      
      if (!data || !Array.isArray(data.events)) {
        throw new Error("Invalid response format from API.");
      }
      
      setEvents(data.events);
    } catch (err: any) {
      setError(err.message || "Failed to load timeline.");
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [domainFilter, typeFilter, offset]);

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto", fontFamily: "sans-serif" }}>
      <h1>Browser Activity Timeline</h1>
      
      <div style={{ marginBottom: "20px", padding: "15px", border: "1px solid #ccc", borderRadius: "5px" }}>
        <h3>Filters</h3>
        <input 
          suppressHydrationWarning
          type="text" 
          placeholder="Filter by domain (e.g. github.com)" 
          value={domainFilter}
          onChange={(e) => setDomainFilter(e.target.value)}
          style={{ marginRight: "10px", padding: "5px" }}
        />
        <input 
          suppressHydrationWarning
          type="text" 
          placeholder="Filter by event type (e.g. page_loaded)" 
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          style={{ padding: "5px" }}
        />
      </div>

      {loading && <div data-testid="loading-state">Loading timeline...</div>}
      
      {error && (
        <div data-testid="error-state" style={{ color: "red", padding: "10px", border: "1px solid red" }}>
          {error}
        </div>
      )}

      {!loading && !error && events.length === 0 && (
        <div data-testid="empty-state">No events found matching your criteria.</div>
      )}

      {!loading && !error && events.length > 0 && (
        <div data-testid="timeline-list">
          {events.map((evt) => (
            <div key={evt.event_id} style={{ borderLeft: "3px solid #007bff", margin: "10px 0", padding: "10px 15px", backgroundColor: "#f9f9f9" }}>
              <div style={{ fontSize: "0.85em", color: "#666" }}>
                {new Date(evt.timestamp).toLocaleString()} | <strong>{evt.domain || "Unknown Domain"}</strong> | {evt.event_type}
              </div>
              <div style={{ margin: "5px 0", fontSize: "1.1em" }}>
                {evt.page_title || evt.url || "Untitled Page"}
              </div>
              {evt.input_text && (
                <div style={{ fontSize: "0.9em", fontStyle: "italic", color: "#444" }}>
                  Input: {evt.input_text}
                </div>
              )}
              {evt.metadata && Object.keys(evt.metadata).length > 0 && (
                <div style={{ marginTop: "8px", padding: "8px", backgroundColor: "#eee", borderRadius: "4px", fontSize: "0.85em", color: "#333", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  <strong>Metadata:</strong><br/>
                  {Object.entries(evt.metadata).map(([key, value]) => (
                    <div key={key}>
                      <span style={{ fontWeight: 600 }}>{key}:</span> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
          
          <div style={{ marginTop: "20px", display: "flex", justifyContent: "space-between" }}>
            <button 
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              style={{ padding: "5px 15px" }}
            >
              Previous
            </button>
            <button 
              onClick={() => setOffset(offset + limit)}
              disabled={events.length < limit}
              style={{ padding: "5px 15px" }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
