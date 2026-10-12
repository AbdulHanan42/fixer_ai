import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("Database_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL in the environment or backend/.env")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
