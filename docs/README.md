# RamGAP Documentation

Overview documentation for the RamGAP platform.

## Contents

- [Architecture](ARCHITECTURE.md) — System design, folder structure, and data flow
- [Contributing](CONTRIBUTING.md) — Code style, adding activities, parking WIP in sandbox

## Quick Start

```bat
cd RamGAP
scripts\start_dev.bat
```

Opens two windows:
- **Backend** — Flask API on `http://localhost:5050`
- **Frontend** — Streamlit UI on `http://localhost:8501`

## Active Activities

| Activity | Backend | Frontend page |
|----------|---------|---------------|
| Projects | `activities/projects/routes.py` | `app.py` (home) |
| Plaxis   | `activities/plaxis/` | `pages/plaxis.py` |
| GeoTolk  | `activities/geotolk/` | `pages/geotolk.py` |
