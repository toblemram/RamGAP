# -*- coding: utf-8 -*-
"""
Database connection and session management for RamGAP
Currently uses SQLite locally, designed for easy migration to Azure SQL
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base

# Database configuration
# Local: SQLite - use absolute path in backend folder
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, 'ramgap.db')

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'sqlite:///{DB_PATH}'
)

# For Azure SQL, use:
# DATABASE_URL = "mssql+pyodbc://username:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if 'sqlite' in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(SessionLocal)


def init_db():
    """Initialize the database, creating all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


def get_db_session():
    """Get a database session"""
    db = Session()
    try:
        return db
    finally:
        pass  # Session will be managed by caller


def close_db_session(db):
    """Close a database session"""
    db.close()


# Dependency for Flask routes
def get_db():
    """Generator for database sessions - use with Flask"""
    db = Session()
    try:
        yield db
    finally:
        db.close()
