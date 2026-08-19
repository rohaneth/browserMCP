import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
import uuid
from db.session import SessionLocal
from models.events import Event

def insert_dummy_events():
    db = SessionLocal()
    events = [
        Event(
            id=1,
            event_id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            event_type="page_loaded",
            url="https://github.com/rohan/mcpmonkey2",
            domain="github.com",
            page_title="Rohan's MCP Monkey Project",
            source="browser_extension",
            schema_version=1
        ),
        Event(
            id=2,
            event_id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            event_type="click",
            url="https://github.com/rohan/mcpmonkey2",
            domain="github.com",
            page_title="Rohan's MCP Monkey Project",
            input_text="Clicked on 'Settings'",
            source="browser_extension",
            schema_version=1
        ),
        Event(
            id=3,
            event_id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            event_type="page_loaded",
            url="https://example.com",
            domain="example.com",
            page_title="Example Domain",
            source="browser_extension",
            schema_version=1
        )
    ]
    
    try:
        for event in events:
            db.add(event)
        db.commit()
        print("Successfully inserted dummy events into the database.")
    except Exception as e:
        db.rollback()
        print(f"Error inserting events: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    insert_dummy_events()
