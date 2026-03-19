# -*- coding: utf-8 -*-
"""
Database Connection
===================
Provides the SQLAlchemy engine, session factory, and helper functions
for creating and accessing the database.

Usage:
    from core.database import init_db, get_db_session

    init_db()
    db = get_db_session()
    try:
        # ... queries ...
    finally:
        db.close()
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from core.models import Base

# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------
# Local development: SQLite file next to backend/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH     = os.path.join(_BACKEND_DIR, 'ramgap.db')

DATABASE_URL: str = os.getenv('DATABASE_URL', f'sqlite:///{_DB_PATH}')

# For Azure SQL, set DATABASE_URL env var:
#   mssql+pyodbc://user:pw@server.database.windows.net:1433/db?driver=ODBC+Driver+18+for+SQL+Server

# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------
_connect_args = {'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session      = scoped_session(SessionLocal)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables if they do not exist yet."""
    Base.metadata.create_all(bind=engine)
    print('Database initialized successfully')


def get_db_session():
    """Return a new database session. Caller is responsible for closing it."""
    return Session()


def close_db_session(db) -> None:
    """Close a database session."""
    db.close()


def get_db():
    """Generator yielding a session (for use with dependency injection)."""
    db = Session()
    try:
        yield db
    finally:
        db.close()
