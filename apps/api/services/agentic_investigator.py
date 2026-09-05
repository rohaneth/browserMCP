import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from groq import Groq

from schemas.structured_output import (
    ConfidenceLevel,
    Citation,
    StructuredToolCall,
    AgenticInvestigationTrace,
    StructuredInvestigationOutput
)
from services.investigation import run_investigation
from services.search import search_events
from services.clustering import InterestClusterEngine
from services.preference import detect_preference_category
from utils.privacy import sanitize_text

logger = logging.getLogger(__name__)

ALLOWED_TOOLS = [
    "search_browser_history",
    "get_timeline",
    "get_domain_statistics",
    "infer_preferences",
    "get_interest_clusters",
    "get_evidence"
]


class AgenticInvestigator:
    """
    Iterative, goal-directed Agentic Investigation Engine.
    Executes a structured loop:
    1. Plan next action / tool call
    2. Execute tool against database
    3. Evaluate evidence sufficiency
    4. Loop if additional context is required (with max step budget & loop protection)
    5. Synthesize structured conclusion with verifiable citations.
    """

    @classmethod
    def run_agentic_loop(
        cls,
        db: Session,
        query: str,
        max_iterations: int = 4
    ) -> StructuredInvestigationOutput:
        step_history: List[StructuredToolCall] = []
        collected_evidence_ids = set()
        citations: List[Citation] = []
        
        tools_used = []
        stop_reason = "max_iterations_reached"

        # Step 1: Initial Investigation using Multi-Route Engine
        step_1_call = StructuredToolCall(
            step_number=1,
            tool_name="multi_route_investigation",
            parameters={"query": query},
            thought_rationale="Launch initial multi-route retrieval to scan entities, preferences, and keywords."
        )
        tools_used.append("multi_route_investigation")

        inv_record, ev_list = run_investigation(db, query)
        for ev in ev_list:
            if ev.event_id not in collected_evidence_ids:
                collected_evidence_ids.add(ev.event_id)
                citations.append(Citation(
                    event_id=ev.event_id,
                    timestamp=ev.timestamp,
                    url=ev.url,
                    title=sanitize_text(ev.title),
                    snippet=sanitize_text(ev.snippet),
                    score=ev.relevance
                ))

        step_1_call.observation_summary = f"Retrieved {len(ev_list)} candidate evidence events."
        step_1_call.evidence_count_gained = len(ev_list)
        step_history.append(step_1_call)

        # Step 2: Agent Reflection & Sufficiency Evaluation
        current_step = 2
        while current_step <= max_iterations:
            # Check if we have sufficient confirmed or strong evidence
            if len(citations) >= 8 or (len(citations) >= 1 and inv_record.status == "completed" and "CONFIRMED" in (inv_record.summary or "")):
                stop_reason = "sufficient_evidence"
                break

            # Need secondary targeted search if broad investigation was thin
            cat_hint = detect_preference_category(query)
            if cat_hint and "interest_clustering" not in tools_used:
                # Drill down via interest clusters
                tool_call = StructuredToolCall(
                    step_number=current_step,
                    tool_name="get_interest_clusters",
                    parameters={"n_clusters": 4},
                    thought_rationale=f"Broad search yielded {len(citations)} records. Checking unsupervised interest clusters to locate contextual patterns."
                )
                tools_used.append("get_interest_clusters")
                clusters = InterestClusterEngine.discover_clusters(db, n_clusters=4)
                tool_call.observation_summary = f"Discovered {len(clusters)} clusters ({', '.join([c.label for c in clusters[:2]])})."
                tool_call.evidence_count_gained = len(clusters)
                step_history.append(tool_call)
                current_step += 1
            else:
                # Secondary keyword fallback search
                words = [w for w in query.split() if len(w) > 3]
                sub_query = words[0] if words else query
                tool_call = StructuredToolCall(
                    step_number=current_step,
                    tool_name="search_browser_history",
                    parameters={"query": sub_query},
                    thought_rationale=f"Deepening search on focal token '{sub_query}'."
                )
                tools_used.append("search_browser_history")
                sec_res = search_events(db, keyword=sub_query)
                new_cnt = 0
                for be in sec_res.events[:5]:
                    eid = str(be.event_id)
                    if eid not in collected_evidence_ids:
                        collected_evidence_ids.add(eid)
                        citations.append(Citation(
                            event_id=eid,
                            timestamp=be.timestamp,
                            url=be.url,
                            title=sanitize_text(be.page_title),
                            snippet=sanitize_text(be.input_text or be.page_title),
                            score=0.75
                        ))
                        new_cnt += 1
                tool_call.observation_summary = f"Secondary search found {sec_res.total} matches ({new_cnt} new citations added)."
                tool_call.evidence_count_gained = new_cnt
                step_history.append(tool_call)
                current_step += 1
                stop_reason = "evidence_search_completed"

        # Classify final confidence
        if any("CONFIRMED" in (inv_record.summary or "") for _ in [1]):
            confidence = ConfidenceLevel.CONFIRMED
        elif len(citations) > 0:
            confidence = ConfidenceLevel.LIKELY
        else:
            confidence = ConfidenceLevel.NOT_FOUND

        trace = AgenticInvestigationTrace(
            query=query,
            total_steps=len(step_history),
            tools_used=tools_used,
            step_history=step_history,
            stop_reason=stop_reason
        )

        return StructuredInvestigationOutput(
            query=query,
            confidence=confidence,
            direct_answer=sanitize_text(inv_record.summary or "Investigation completed."),
            key_findings=[f"Evidence citations retrieved: {len(citations)}", f"Agent iterations: {len(step_history)}"],
            citations=citations[:20],
            trace=trace,
            structured_metadata={"strategy": inv_record.plan.get("retrieval_strategy") if inv_record.plan else "agentic"}
        )
