import sys
import os
import json

# Setup paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'mcp')))

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

questions = [
    ("1. Favourite programming language", lambda: execute_investigate("what is my favourite programming language")),
    ("2. What I searched on Stack Overflow", lambda: execute_investigate("what did I search on Stack Overflow")),
    ("3. Today's sessions / Sessions analysis", lambda: execute_get_sessions(limit=5)),
    ("4. Most visited website this week / Domain statistics", lambda: execute_get_domain_statistics(limit=5)),
    ("5. This week vs last week activity comparison", lambda: execute_compare_time_periods(
        period_a_start="2026-08-16T00:00:00",
        period_a_end="2026-08-16T23:59:59",
        period_b_start="2026-08-15T00:00:00",
        period_b_end="2026-08-15T23:59:59",
        label_a="Aug 16",
        label_b="Aug 15"
    )),
    ("6. Why Java appears to be my favourite", lambda: execute_investigate("why does Java appear to be my favourite programming language")),
    ("7. What I did yesterday afternoon / timeline search", lambda: execute_investigate("what did I do yesterday afternoon")),
    ("8. Longest session last week", lambda: execute_get_sessions(limit=10)),
    ("9. Behavioral patterns (peak hours, weekdays)", lambda: execute_get_behavioral_patterns()),
    ("10. Specific evidence verification", lambda: execute_search_history(query="stackoverflow", limit=2))
]

print("=" * 80)
print("RUNNING BROWSERMCP VERIFICATION ON EXAMPLE QUESTIONS")
print("=" * 80)

for title, fn in questions:
    print(f"\n--- {title} ---")
    try:
        res = fn()
        # Print a concise representation of the response
        if "answer" in res:
            print(f"[Answer]:\n{res['answer']}\n")
            print(f"[Evidence Count]: {res.get('evidence_count', 0)}")
        elif "sessions" in res:
            print(f"[Sessions Found]: {res['total_sessions']}")
            for s in res['sessions'][:2]:
                print(f"  - Session ID: {s['session_id']} | Duration: {s['duration_human']} | Events: {s['event_count']} | Activity: {s['dominant_activity']}")
        elif "domains" in res:
            print(f"[Top Domains Found]: {len(res['domains'])}")
            for d in res['domains'][:3]:
                queries_safe = [q.encode('ascii', 'replace').decode('ascii') for q in d['searches_conducted']]
                print(f"  - {d['domain']}: {d['total_events']} events, {d['unique_pages_count']} unique pages. Queries: {queries_safe}")
        elif "comparison" in res:
            print(f"[Comparison Summary Insights]: {res['summary_insights']}")
        elif "peak_time_of_day" in res:
            print(f"[Peak Browsing]: {res['peak_time_of_day']} (UTC {res['peak_hour_utc']}) on {res['peak_active_day']} (Analyzed {res['total_events_analyzed']} events)")
        elif "events" in res:
            print(f"[Search Matches]: {res['returned_count']} of {res['total_matches']}")
            for ev in res['events'][:2]:
                print(f"  - [{ev['timestamp']}] {ev['domain']} : {ev['page_title']} (URL: {ev['url']})")
        else:
            print(json.dumps(res, indent=2)[:300] + "...")
        print("[Status]: SUCCESS")
    except Exception as e:
        print(f"[Status]: FAILED - {e}")

print("\n" + "=" * 80)
print("ALL VERIFICATIONS COMPLETED")
print("=" * 80)
