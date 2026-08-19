import os
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres_password@localhost:5432/browser_agent_db"
import sys
import sqlalchemy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.session import engine, Base
import models.events
import models.sessions
import models.memories
import models.settings

with engine.connect() as conn:
    conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS events CASCADE;"))
    conn.commit()

Base.metadata.create_all(bind=engine)
print("Events table dropped and recreated successfully with new schema!")
