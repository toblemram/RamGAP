# -*- coding: utf-8 -*-
"""
Application Configuration
=========================
Loads all environment variables and exposes application-wide constants.
Import from here instead of reading os.environ directly in other modules.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# --- Server ---
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
HOST  = os.getenv("HOST", "0.0.0.0")
PORT  = int(os.getenv("PORT", "5050"))

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ramgap.db")

# --- Plaxis ---
PLAXIS_HOST         = os.getenv("PLAXIS_HOST", "localhost")
PLAXIS_DEFAULT_PORT = int(os.getenv("PLAXIS_DEFAULT_PORT", "10000"))

# --- OpenAI / AI Assistant ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o")
EMBED_MODEL    = os.getenv("EMBED_MODEL", "text-embedding-3-large")

# --- Azure Blob Storage ---
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
AZURE_STORAGE_CONTAINER         = os.getenv('AZURE_STORAGE_CONTAINER', 'project-files')
AZURE_STORAGE_TEMP_CONTAINER    = os.getenv('AZURE_STORAGE_TEMP_CONTAINER', 'temp-uploads')

# --- Knowledge Base ---
KNOWLEDGE_DIR  = os.getenv("KNOWLEDGE_DIR", "plaxis_knowledge")
FAISS_IDX_FULL  = os.getenv("FAISS_IDX_FULL",  "faiss_full.index")
FAISS_IDX_SHORT = os.getenv("FAISS_IDX_SHORT", "faiss_short.index")
DOC_IDS_FILE    = os.getenv("DOC_IDS_FILE",    "doc_ids.json")
