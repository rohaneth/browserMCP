import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Fallback to SQLite so the user can see the UI without Postgres setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./demo.db",
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Monkey-patch JSONB for SQLite globally for demo
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from pgvector.sqlalchemy import Vector
@compiles(Vector, 'sqlite')
def compile_vector_sqlite(type_, compiler, **kw):
    return "JSON"

# Initialize tables
from models.base import Base
import models.events
import models.sessions
import models.memories
import models.settings
import models.investigations

if not DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
