# plaxchat2

Advanced Plaxis chat prototype with Retrieval-Augmented Generation (RAG).
Uses a FAISS vector index over Plaxis API documentation for more accurate
and grounded code generation.

## Status

Prototype — the indexing and retrieval logic is being migrated into
`backend/activities/ai_assistant/knowledge/`.

## Structure

```
plaxchat2/
├── plaxis_assistant.py  — Main CustomTkinter app
├── indexing/            — FAISS index builder
└── retrieval/           — Hybrid search
```

## Usage

```bash
pip install -r requirements.txt
python plaxis_assistant.py
```
