"use client";

import React, { useState, useRef, useEffect } from "react";
import Head from "next/head";

interface Evidence {
  event_id: string;
  timestamp: string;
  url?: string;
  title?: string;
  snippet: string;
  relevance: number;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  evidence?: Evidence[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const url = process.env.NEXT_PUBLIC_API_URL 
        ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1/query` 
        : 'http://localhost:8000/api/v1/query';

      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg.content }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMsg: Message = { 
        id: (Date.now() + 1).toString(), 
        role: "assistant", 
        content: data.answer || "I could not synthesize an answer.",
        evidence: data.evidence || []
      };
      
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev, 
        { id: (Date.now() + 1).toString(), role: "assistant", content: `Error: ${err.message}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>BrowserMCP | Intelligence Chat</title>
        <meta name="description" content="Chat with your browser intelligence agent." />
      </Head>
      
      <style dangerouslySetInnerHTML={{__html: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        
        body {
          margin: 0;
          background: #0f172a;
          color: #f8fafc;
          font-family: 'Inter', sans-serif;
        }
        
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 100vh;
          max-width: 900px;
          margin: 0 auto;
          background: linear-gradient(145deg, rgba(30,41,59,0.7) 0%, rgba(15,23,42,0.9) 100%);
          box-shadow: 0 0 40px rgba(0,0,0,0.5);
        }

        .chat-header {
          padding: 24px;
          background: rgba(30, 41, 59, 0.5);
          backdrop-filter: blur(12px);
          border-bottom: 1px solid rgba(255,255,255,0.1);
          text-align: center;
          font-weight: 600;
          letter-spacing: 1px;
          font-size: 1.2rem;
          color: #38bdf8;
        }

        .messages-area {
          flex: 1;
          overflow-y: auto;
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .message-bubble {
          max-width: 80%;
          padding: 16px 20px;
          border-radius: 16px;
          line-height: 1.5;
          animation: fadeIn 0.3s ease-out forwards;
          box-shadow: 0 4px 15px rgba(0,0,0,0.1);
          white-space: pre-wrap;
        }

        .message-user {
          align-self: flex-end;
          background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
          color: white;
          border-bottom-right-radius: 4px;
        }

        .message-assistant {
          align-self: flex-start;
          background: rgba(51, 65, 85, 0.7);
          backdrop-filter: blur(8px);
          border: 1px solid rgba(255,255,255,0.05);
          border-bottom-left-radius: 4px;
        }

        .evidence-container {
          margin-top: 14px;
          padding-top: 10px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          font-size: 0.85rem;
        }

        .evidence-title {
          font-weight: 600;
          color: #38bdf8;
          margin-bottom: 8px;
        }

        .evidence-item {
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 8px;
          padding: 8px 12px;
          margin-bottom: 6px;
        }

        .evidence-link {
          color: #7dd3fc;
          font-size: 0.78rem;
          text-decoration: underline;
          word-break: break-all;
        }

        .input-area {
          padding: 20px;
          background: rgba(15, 23, 42, 0.8);
          backdrop-filter: blur(12px);
          border-top: 1px solid rgba(255,255,255,0.05);
        }

        .input-form {
          display: flex;
          gap: 12px;
          position: relative;
        }

        .chat-input {
          flex: 1;
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 24px;
          padding: 16px 24px;
          color: white;
          font-size: 1rem;
          font-family: 'Inter', sans-serif;
          transition: all 0.3s ease;
        }

        .chat-input:focus {
          outline: none;
          border-color: #38bdf8;
          box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
          background: rgba(30, 41, 59, 0.9);
        }

        .send-button {
          background: #38bdf8;
          color: #0f172a;
          border: none;
          border-radius: 24px;
          padding: 0 24px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .send-button:hover:not(:disabled) {
          background: #7dd3fc;
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(56, 189, 248, 0.4);
        }

        .send-button:disabled {
          background: #475569;
          color: #94a3b8;
          cursor: not-allowed;
        }

        .typing-indicator {
          display: flex;
          gap: 4px;
          padding: 8px 0;
        }

        .dot {
          width: 8px;
          height: 8px;
          background: #94a3b8;
          border-radius: 50%;
          animation: bounce 1.4s infinite ease-in-out both;
        }

        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}} />

      <div className="chat-container">
        <div className="chat-header">
          ✦ Browser Intelligence Agent
        </div>

        <div className="messages-area">
          {messages.length === 0 && (
            <div style={{ textAlign: "center", color: "#64748b", marginTop: "40px" }}>
              <div style={{ fontSize: "3rem", marginBottom: "16px" }}>👋</div>
              <h2>Ask me anything about your browsing history</h2>
              <p>Try: "What did I type on Stack Overflow?" or "What websites do I visit most?"</p>
            </div>
          )}

          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`message-bubble ${msg.role === 'user' ? 'message-user' : 'message-assistant'}`}
            >
              {msg.content}

              {msg.role === 'assistant' && msg.evidence && msg.evidence.length > 0 && (
                <div className="evidence-container">
                  <div className="evidence-title">
                    🔍 Evidence & Source Records ({msg.evidence.length})
                  </div>
                  <div className="evidence-list">
                    {msg.evidence.slice(0, 5).map((ev) => (
                      <div key={ev.event_id} className="evidence-item">
                        <div style={{ fontWeight: 600, color: "#e2e8f0" }}>{ev.title || "Untitled Page"}</div>
                        <div style={{ color: "#94a3b8", fontSize: "0.78rem" }}>{ev.snippet}</div>
                        {ev.url && (
                          <a href={ev.url} target="_blank" rel="noopener noreferrer" className="evidence-link">
                            {ev.url}
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="message-bubble message-assistant">
              <div className="typing-indicator">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <form className="input-form" onSubmit={handleSubmit}>
            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Query your personal browser memory..."
              disabled={isLoading}
            />
            <button type="submit" className="send-button" disabled={isLoading || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
