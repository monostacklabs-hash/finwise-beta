"""
Database session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from ..config import settings

# Create engine with optimized connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Check connection health before using
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=10,  # Max connections in pool
    max_overflow=20,  # Max overflow connections beyond pool_size
    pool_timeout=30,  # Timeout for getting connection from pool (seconds)
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from .exceptions import DatabaseOperationError

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session
    Provides robust session management with error handling
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Explicit commit
    except SQLAlchemyError as e:
        # Rollback in case of any database error
        db.rollback()
        # Convert SQLAlchemy error to our custom exception
        raise DatabaseOperationError(
            message="Database transaction failed",
            operation="get_db",
            details=str(e)
        ) from e
    finally:
        db.close()

@contextmanager
def db_transaction(db: Session):
    """
    Context manager for database transactions with automatic rollback on error

    Usage:
        with db_transaction(db) as transaction:
            # Perform database operations
            # No need to manually commit or rollback
    """
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseOperationError(
            message="Database transaction failed",
            operation="db_transaction",
            details=str(e)
        ) from e


def init_db():
    """Initialize database (create tables)"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
