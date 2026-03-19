# -*- coding: utf-8 -*-
"""
Knowledge Base Indexer
=======================
Reads Plaxis API documentation JSON files, generates embeddings via OpenAI,
and writes short and full FAISS indexes to disk.

Run this script whenever the knowledge base is updated:
    python -m activities.ai_assistant.knowledge.indexer

TODO: Move logic from prototype/PlaxChat2/indexing/indexer.py here.
"""
