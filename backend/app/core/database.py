from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv
import os

root_env = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if root_env.exists():
    load_dotenv(root_env)
load_dotenv()

db_url = os.getenv("DATABASE_URL")
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = db_url
else:
    user = os.getenv("POSTGRES_DB_USER", "mandateguard")
    password = os.getenv("POSTGRES_DB_PASSWORD", "")
    host = os.getenv("POSTGRES_DB_HOST", "localhost")
    port = os.getenv("POSTGRES_DB_PORT", "5432")
    name = os.getenv("POSTGRES_DB_NAME", "mandateguard")
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{name}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
