# -*- coding: utf-8 -*-
"""
Database Connection
===================
Dual-database setup:
  - **Main DB** (Azure PostgreSQL via DATABASE_URL):
    Projects, activity logs, GeoTolk sessions/interpretations, Plaxis calculations.
  - **ML DB** (Azure PostgreSQL via ML_DATABASE_URL):
    Dedicated ML training data (GeoTolkMLTrainingData) for model training.

Usage:
    from core.database import init_db, get_db_session, get_ml_session

    init_db()
    db = get_db_session()        # main app data
    ml = get_ml_session()        # ML training data only
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from core.models import Base, MLBase

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Main database (projects, sessions, logs, interpretations) — Azure PostgreSQL
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.environ['DATABASE_URL']

engine = create_engine(
    DATABASE_URL,
    connect_args={'connect_timeout': 5},
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session      = scoped_session(SessionLocal)

# ---------------------------------------------------------------------------
# ML training database (Azure PostgreSQL — dedicated for ML data)
# ---------------------------------------------------------------------------
ML_DATABASE_URL: str = os.environ['ML_DATABASE_URL']

ml_engine = create_engine(
    ML_DATABASE_URL,
    connect_args={'connect_timeout': 10},
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True,
    echo=False,
)
MLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ml_engine)
MLSession      = scoped_session(MLSessionLocal)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables in both main and ML databases."""
    from sqlalchemy import inspect as sa_inspect, text

    # --- Main database ---
    Base.metadata.create_all(bind=engine)

    insp = sa_inspect(engine)
    if 'projects' in insp.get_table_names():
        cols = [c['name'] for c in insp.get_columns('projects')]
        if 'project_owner' not in cols:
            with engine.begin() as conn:
                conn.execute(text('ALTER TABLE projects ADD COLUMN project_owner VARCHAR(255)'))
            print('Migration: added project_owner column to projects')
        if 'folder_path' not in cols:
            with engine.begin() as conn:
                conn.execute(text('ALTER TABLE projects ADD COLUMN folder_path VARCHAR(500)'))
            print('Migration: added folder_path column to projects')

    if 'geotolk_interpretations' in insp.get_table_names():
        cols = [c['name'] for c in insp.get_columns('geotolk_interpretations')]
        if 'has_oedometer' not in cols:
            with engine.begin() as conn:
                conn.execute(text(
                    'ALTER TABLE geotolk_interpretations ADD COLUMN has_oedometer BOOLEAN DEFAULT FALSE'
                ))
            print('Migration: added has_oedometer column to geotolk_interpretations')
        if 'snd_raw_content' not in cols:
            with engine.begin() as conn:
                conn.execute(text(
                    'ALTER TABLE geotolk_interpretations ADD COLUMN snd_raw_content TEXT'
                ))
            print('Migration: added snd_raw_content column to geotolk_interpretations')

    print(f'Main database initialized ({DATABASE_URL[:40]}...)')

    # --- ML database ---
    MLBase.metadata.create_all(bind=ml_engine)
    print(f'ML database initialized ({ML_DATABASE_URL[:40]}...)')


def get_db_session():
    """Return a main database session. Caller is responsible for closing it."""
    return Session()


def get_ml_session():
    """Return an ML database session."""
    return MLSession()



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
