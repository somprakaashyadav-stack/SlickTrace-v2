from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging
from backend.config import settings

logger = logging.getLogger("slicktrace.database")

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite"):
        logger.info(f"Using SQLite Database fallback: {db_url}")
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
    else:
        logger.info(f"Using PostgreSQL + PostGIS Database: {db_url}")
        return create_engine(db_url, pool_pre_ping=True)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization error (proceeding with fallback): {e}")
