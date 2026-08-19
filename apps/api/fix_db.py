import os
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres_password@localhost:5432/browser_agent_db"
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.session import engine, Base
import models.events
import models.sessions
import models.memories
import models.settings
Base.metadata.create_all(bind=engine)
print("Tables created successfully in Postgres!")
