# RamGAP

Prosjektstruktur med Flask backend, Streamlit frontend og lokal SQLite database.

## Struktur

```
RamGAP/
├── backend/
│   ├── app.py              # Flask API server
│   └── database/
│       ├── __init__.py
│       ├── db.py           # Database connection
│       └── models.py       # SQLAlchemy models
├── frontend/
│   └── app.py              # Streamlit UI
├── requirements.txt
└── README.md
```

## Installasjon

```bash
# Opprett og aktiver virtuelt miljø
python -m venv .venv
.venv\Scripts\activate  # Windows

# Installer avhengigheter
pip install -r requirements.txt
```

## Kjøring

### Start Backend (Flask)
```bash
cd backend
python app.py
```
Backend kjører på http://localhost:5000

### Start Frontend (Streamlit)
```bash
cd frontend
streamlit run app.py
```
Frontend kjører på http://localhost:8501

## Database

Lokal utvikling bruker SQLite (`ramgap.db`).

For Azure SQL, oppdater `DATABASE_URL` i `backend/database/db.py`:
```python
DATABASE_URL = "mssql+pyodbc://username:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server"
```

## API Endepunkter

| Metode | Endepunkt | Beskrivelse |
|--------|-----------|-------------|
| GET | `/api/health` | Helsesjekk |
| GET | `/api/status` | Applikasjonsstatus |
| GET | `/api/data` | Hent data |
| POST | `/api/data` | Opprett data |

## Status

🚀 **Klar til videre utvikling**
