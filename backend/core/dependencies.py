"""
Database dependencies
Centralized database session management
"""
from database import SessionLocal


def get_db():
    """
    Database session dependency
    Yields a database session and ensures it's closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
