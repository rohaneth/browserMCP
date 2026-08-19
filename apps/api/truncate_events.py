import os
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres_password@localhost:5432/browser_agent_db"
import sys
import sqlalchemy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.session import engine

with engine.connect() as conn:
    conn.execute(sqlalchemy.text("TRUNCATE TABLE events CASCADE;"))
    conn.commit()

print("Events table truncated successfully!")
