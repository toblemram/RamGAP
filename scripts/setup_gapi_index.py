# -*- coding: utf-8 -*-
"""
Setup script: create Azure resources for GAPI PLAXIS manual indexing.

Run from the RamGAP/RamGAP/backend directory:
    python ../scripts/setup_gapi_index.py
"""
import sys
import os

# Make sure we can import backend modules
_backend = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, os.path.normpath(_backend))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

BLOB_CONN  = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
CONTAINER  = os.getenv('GAPI_BLOB_CONTAINER', 'gapi-plaxis-manual')
PDF_PATH   = os.path.join(os.path.dirname(__file__), '..', 'docs',
                          'PLAXIS_2D_1_Tutorial Manual (1).pdf')

# ── Step 1: Create blob container ───────────────────────────────────────────
print('\n=== Steg 1: Oppretter blob-container ===')
from azure.storage.blob import BlobServiceClient
svc = BlobServiceClient.from_connection_string(BLOB_CONN)
try:
    svc.create_container(CONTAINER)
    print(f'  Container "{CONTAINER}" opprettet.')
except Exception as e:
    print(f'  Container eksisterer allerede eller feil: {e}')

# ── Step 2: Set up Azure AI Search index + datasource + indexer ─────────────
print('\n=== Steg 2: Oppretter Azure AI Search-indeks, datakilde og indekserer ===')
from activities.plaxis_agent.indexer import full_setup
results = full_setup()
for key, val in results.items():
    print(f'  {key}: {val}')

# ── Step 3: Upload PLAXIS manual PDF ────────────────────────────────────────
print('\n=== Steg 3: Laster opp PLAXIS Tutorial Manual PDF ===')
pdf_path = os.path.normpath(PDF_PATH)
if not os.path.isfile(pdf_path):
    print(f'  FEIL: Fant ikke PDF på {pdf_path}')
    sys.exit(1)

filename = os.path.basename(pdf_path)
with open(pdf_path, 'rb') as f:
    data = f.read()

bc = svc.get_blob_client(container=CONTAINER, blob=filename)
bc.upload_blob(data, overwrite=True)
print(f'  Lastet opp "{filename}" ({len(data) / 1024 / 1024:.1f} MB)')

# ── Step 4: Trigger reindexing ───────────────────────────────────────────────
print('\n=== Steg 4: Starter indeksering ===')
from activities.plaxis_agent.indexer import run_indexer
result = run_indexer()
print(f'  {result}')

print('\n✓ Ferdig! Indeksering av PLAXIS-manualen er startet.')
print('  Bruk GET /api/plaxis-agent/manual/status for å sjekke fremgangen.')
