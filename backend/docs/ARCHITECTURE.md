# Architecture

RamGAP is a geotechnical engineering platform with a clear separation between
backend services, frontend UI, and sandbox scripts.

## Stack

| Layer    | Technology              | Location          |
|----------|-------------------------|-------------------|
| Backend  | Flask REST API (Python) | `backend/`        |
| Frontend | Streamlit (Python)      | `frontend/`       |
| Database | SQLite / Azure SQL      | `backend/core/`   |
| Sandbox  | Standalone scripts      | `sandbox/`        |

## Backend Structure

```
backend/
├── app.py                    # Flask entry point — registers all blueprints
├── core/
│   ├── models.py             # SQLAlchemy ORM models
│   └── database.py           # DB engine, session factory, init_db()
├── shared/                   # Reusable utilities (helpers, validators)
└── activities/               # One folder per feature area
    ├── projects/
    │   └── routes.py         # /api/projects CRUD + /api/activity log
    ├── plaxis/
    │   ├── routes.py         # /api/plaxis/* endpoints
    │   ├── service.py        # PlaxisService — connect/disconnect/model info
    │   ├── runner/
    │   │   └── runner.py     # Orchestrates full extraction run
    │   └── extraction/
    │       ├── level1_info.py
    │       ├── level5_results.py
    │       ├── level5_data.py
    │       └── level5_print.py
    └── geotolk/
        ├── routes.py         # /api/geotolk/* endpoints
        ├── service.py        # GeoTolkService
        ├── parsing/
        │   └── snd_parser.py # SND file parser
        └── visualization/    # Chart helpers
```

## Frontend Structure

```
frontend/
├── app.py                    # Home page, project list, project view, setup
├── config.py                 # Shared constants (API base URL, etc.)
├── components/
│   ├── api_client.py         # APIClient — all HTTP calls to the backend
│   ├── sidebar.py            # Shared sidebar component
│   └── project_selector.py
└── pages/
    ├── plaxis.py             # Full 5-level Plaxis automation workflow
    └── geotolk.py            # SND file upload, parsing, and interpretation
```

## Sandbox

Experimental and archived scripts that are not part of the active application:

```
sandbox/
├── ai_assistant/   # Parked LLM assistant (routes, service, indexer)
├── plaxis_scripts/ # Early standalone Plaxis extraction scripts
├── chatplax/       # Early chat prototype
├── plaxchat2/      # Improved chat prototype
├── pyqt_prototype/ # Desktop GUI prototype
└── tolkboss/       # Standalone SND viewer tool
```

## Data Flow

```
User → Streamlit (frontend) → Flask API (backend) → Activity Service → DB / Plaxis
```
