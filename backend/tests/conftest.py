import pytest
from typing import Generator
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import Base

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    # Bind existing tables and open a test session
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()