import sys
sys.path.append('apps/api')
from database.session import SessionLocal
from services.search import search_events, search_hybrid
db = SessionLocal()
res = search_events(db, "test")
print("search_events res:", repr(res))
if res is not None:
    print("res.events type:", type(res.events))
try:
    h_res = search_hybrid(db, "test")
    print("search_hybrid res:", h_res)
except Exception as e:
    print("Error in search_hybrid:", repr(e))
