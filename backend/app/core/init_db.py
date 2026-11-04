from app.core.database import engine
from app.models import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating database tables in PostgreSQL...")
    init_db()
    print("Tables created successfully!")