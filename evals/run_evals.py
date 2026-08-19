import json
import os
import sys

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from db.session import SessionLocal
from services.search import search_hybrid

def run_evaluations():
    dataset_path = os.path.join(os.path.dirname(__file__), 'golden_dataset.json')
    if not os.path.exists(dataset_path):
        print("Golden dataset not found.")
        return

    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    db = SessionLocal()
    total = len(dataset)
    passed = 0

    try:
        for item in dataset:
            query = item['query']
            print(f"Evaluating query: {query}")
            
            # Using hybrid search to get top results
            res = search_hybrid(db, query, limit=5)
            top_results = res.get("top_results", [])
            
            # Simple Recall check
            expected = set(item.get('expected_events', []))
            retrieved = set(top_results)
            
            if expected and expected.issubset(retrieved):
                print("  [PASS] Expected events retrieved.")
                passed += 1
            else:
                print(f"  [FAIL] Missing expected events. Expected: {expected}, Retrieved: {retrieved}")
                
        print(f"\nEvaluation Summary: {passed}/{total} passed ({(passed/total)*100:.1f}%)")

    finally:
        db.close()

if __name__ == "__main__":
    run_evaluations()
