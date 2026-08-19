import sys
import os
import json
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ["DATABASE_URL"] = "sqlite:///./demo.db"

from db.session import engine, Base, SessionLocal
import models.events
import models.sessions
import models.memories
import models.settings
import models.investigations
from models.events import Event
from utils.normalization import extract_url_search_params

print("Recreating database schema in demo.db...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

log_path = os.path.join(os.path.dirname(__file__), '..', '..', 'events.log')
db = SessionLocal()

imported = 0
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            
            event_type = data.get('event') or data.get('type') or 'unknown'
            page_title = data.get('pageTitle') or data.get('title') or ''
            input_text = data.get('input') or data.get('text') or ''
            url = data.get('url', '')
            domain = ''
            if url:
                try:
                    domain = urlparse(url).netloc
                except Exception:
                    pass
            
            if not input_text and url:
                extracted_search = extract_url_search_params(url)
                if extracted_search:
                    input_text = extracted_search
            
            ts_str = data.get('timestamp')
            if not ts_str:
                ts = datetime.now(timezone.utc)
            else:
                try:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                except Exception:
                    ts = datetime.now(timezone.utc)

            ev = Event(
                event_id=uuid.uuid4(),
                timestamp=ts,
                event_type=event_type,
                url=url,
                canonical_url=url,
                domain=domain,
                page_title=page_title,
                content=data.get('content', ''),
                input_text=input_text,
                source='events_log',
                schema_version=1
            )
            db.add(ev)
            imported += 1
    
    try:
        db.commit()
        print(f"Successfully seeded {imported} events from events.log into demo.db!")
    except Exception as e:
        db.rollback()
        print(f"Error committing seeded events: {e}")
    finally:
        db.close()
else:
    print(f"events.log not found at {log_path}")
