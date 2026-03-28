from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
import os
from dotenv import load_dotenv


load_dotenv()

# local PostgreSQL connection string
# Format: postgresql://username:password@localhost:5432/db_name
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/astrologic")

# Engine: the database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal: the factory for creating new database sessions. Each session is a transactional scope for database operations.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: the base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Dependency to manage database sessions in FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()