# -*- coding: utf-8 -*-
"""
GeoGPT Routes
=============
Flask Blueprint with REST API endpoints for the GeoGPT knowledge base.

Endpoints:
    GET  /api/geogpt/knowledge              — List all knowledge entries (with optional search)
    GET  /api/geogpt/knowledge/<id>         — Get a single entry
    POST /api/geogpt/knowledge              — Create a new entry (admin)
    PUT  /api/geogpt/knowledge/<id>         — Update an entry (admin)
    DELETE /api/geogpt/knowledge/<id>       — Delete an entry (admin)
    GET  /api/geogpt/categories             — List available categories
    POST /api/geogpt/chat                   — Simple knowledge-based chat
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from openai import AzureOpenAI

geogpt_bp = Blueprint('geogpt', __name__, url_prefix='/api/geogpt')

# Path to the JSON knowledge base
_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
_KNOWLEDGE_FILE = os.path.join(_DATA_DIR, 'geogpt_knowledge.json')

# Admin users who can edit knowledge (simple JSON-file approach)
_ADMIN_FILE = os.path.join(_DATA_DIR, 'geogpt_admins.json')

# Azure OpenAI settings
_AZURE_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', '')
_AZURE_KEY = os.getenv('AZURE_OPENAI_API_KEY', '')
_AZURE_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
_DEPLOYMENT = os.getenv('GEOGPT_DEPLOYMENT') or os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o')
_SYSTEM_PROMPT = os.getenv(
    'GEOGPT_SYSTEM_PROMPT',
    'Du er GeoGPT, en ekspert-assistent for geoteknikk. Svar alltid på norsk. '
    'Baser svarene dine på dokumentene gitt som kontekst. '
    'Gi korte, presise svar med fagterminologi. Bruk punktlister der det passer. '
    'Unngå lange innledninger — gå rett på sak. '
    'Hvis konteksten ikke dekker spørsmålet, si kort fra og gi et konsist svar '
    'basert på generell geoteknisk kunnskap.'
)

# Azure AI Search settings
_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT', '')
_SEARCH_KEY = os.getenv('AZURE_SEARCH_KEY', '')
_SEARCH_INDEX = os.getenv('AZURE_SEARCH_INDEX', 'geogpt-knowledge')


def _get_ai_client() -> AzureOpenAI | None:
    """Return an Azure OpenAI client, or None if not configured."""
    if not _AZURE_ENDPOINT or not _AZURE_KEY:
        return None
    return AzureOpenAI(
        azure_endpoint=_AZURE_ENDPOINT,
        api_key=_AZURE_KEY,
        api_version=_AZURE_API_VERSION,
    )


def _get_search_client():
    """Return an Azure AI Search client, or None if not configured."""
    if not _SEARCH_ENDPOINT or not _SEARCH_KEY:
        return None
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        return SearchClient(
            endpoint=_SEARCH_ENDPOINT,
            index_name=_SEARCH_INDEX,
            credential=AzureKeyCredential(_SEARCH_KEY),
        )
    except Exception:
        return None


# Blob storage settings for GeoGPT documents
_BLOB_CONN_STR = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
_GEOGPT_CONTAINER = os.getenv('GEOGPT_BLOB_CONTAINER', 'geogpt-knowledge')


def _search_documents(question: str, top: int = 5) -> tuple[list[dict], str | None]:
    """Search Azure AI Search index. Returns (docs, error_message)."""
    client = _get_search_client()
    if not client:
        return [], 'Azure AI Search er ikke konfigurert (mangler AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_KEY)'

    def _parse_results(results) -> list[dict]:
        docs = []
        for r in results:
            source = r.get('source') or r.get('metadata_storage_name', '')
            title  = r.get('title') or r.get('metadata_storage_name', '') or source
            docs.append({
                'content': r.get('content', ''),
                'title': title,
                'source': source,
                'score': r.get('@search.reranker_score') or r.get('@search.score', 0),
            })
        return docs

    # Try semantic search first, fall back to simple if not available
    for query_type, extra in [
        ('semantic', {'semantic_configuration_name': 'default'}),
        ('simple',   {}),
    ]:
        try:
            results = client.search(
                search_text=question,
                top=top,
                query_type=query_type,
                **extra,
            )
            docs = _parse_results(results)
            return docs, None
        except Exception as exc:
            err_str = str(exc)
            if query_type == 'semantic':
                print(f'GeoGPT semantic search failed, retrying simple: {err_str}')
                continue
            print(f'GeoGPT search error: {err_str}')
            return [], f'Søk feilet: {err_str[:200]}'

    return [], 'Søk feilet etter alle forsøk'


def _get_blob_sas_url(blob_name: str, expiry_hours: int = 1) -> str:
    """Generate a time-limited SAS URL for a GeoGPT document blob."""
    if not _BLOB_CONN_STR:
        return ''
    try:
        from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
        svc = BlobServiceClient.from_connection_string(_BLOB_CONN_STR)
        sas = generate_blob_sas(
            account_name=svc.account_name,
            container_name=_GEOGPT_CONTAINER,
            blob_name=blob_name,
            account_key=svc.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        )
        return (
            f'https://{svc.account_name}.blob.core.windows.net'
            f'/{_GEOGPT_CONTAINER}/{blob_name}?{sas}'
        )
    except Exception as exc:
        print(f"GeoGPT SAS URL error: {exc}")
        return ''


def _load_knowledge() -> dict:
    """Load knowledge base from JSON file."""
    with open(_KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_knowledge(data: dict) -> None:
    """Persist knowledge base to JSON file."""
    with open(_KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_admins() -> list[str]:
    """Return list of admin usernames."""
    if not os.path.exists(_ADMIN_FILE):
        return []
    with open(_ADMIN_FILE, 'r', encoding='utf-8') as f:
        return json.load(f).get('admins', [])


def _is_admin(username: str) -> bool:
    """Check if a username has admin access."""
    return username.upper() in [a.upper() for a in _get_admins()]


# ------------------------------------------------------------------
# Categories
# ------------------------------------------------------------------

@geogpt_bp.route('/categories', methods=['GET'])
def get_categories():
    """Return the list of available knowledge categories."""
    data = _load_knowledge()
    return jsonify({'categories': data.get('categories', [])})


# ------------------------------------------------------------------
# Knowledge CRUD
# ------------------------------------------------------------------

@geogpt_bp.route('/knowledge', methods=['GET'])
def list_knowledge():
    """List all knowledge entries. Supports ?q= for text search and ?category= for filtering."""
    data = _load_knowledge()
    entries = data.get('entries', [])

    # Optional text search
    q = request.args.get('q', '').strip().lower()
    if q:
        entries = [
            e for e in entries
            if q in e.get('question', '').lower()
            or q in e.get('answer', '').lower()
            or q in ' '.join(e.get('tags', [])).lower()
        ]

    # Optional category filter
    category = request.args.get('category', '').strip()
    if category:
        entries = [e for e in entries if e.get('category', '').lower() == category.lower()]

    return jsonify({'entries': entries, 'total': len(entries)})


@geogpt_bp.route('/knowledge/<entry_id>', methods=['GET'])
def get_knowledge(entry_id: str):
    """Get a single knowledge entry by ID."""
    data = _load_knowledge()
    for entry in data.get('entries', []):
        if entry['id'] == entry_id:
            return jsonify(entry)
    return jsonify({'error': 'Entry not found'}), 404


@geogpt_bp.route('/knowledge', methods=['POST'])
def create_knowledge():
    """Create a new knowledge entry. Requires admin access."""
    body = request.get_json() or {}
    username = body.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    question = body.get('question', '').strip()
    answer = body.get('answer', '').strip()
    category = body.get('category', 'Generelt')
    tags = body.get('tags', [])

    if not question or not answer:
        return jsonify({'error': 'Spørsmål og svar er obligatorisk'}), 400

    data = _load_knowledge()
    now = datetime.now(timezone.utc).isoformat()
    new_entry = {
        'id': str(uuid.uuid4())[:8],
        'question': question,
        'answer': answer,
        'category': category,
        'tags': tags if isinstance(tags, list) else [t.strip() for t in tags.split(',') if t.strip()],
        'created_by': username,
        'created_at': now,
        'updated_at': now,
    }
    data['entries'].append(new_entry)
    _save_knowledge(data)
    return jsonify({'success': True, 'entry': new_entry}), 201


@geogpt_bp.route('/knowledge/<entry_id>', methods=['PUT'])
def update_knowledge(entry_id: str):
    """Update an existing knowledge entry. Requires admin access."""
    body = request.get_json() or {}
    username = body.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    data = _load_knowledge()
    for entry in data.get('entries', []):
        if entry['id'] == entry_id:
            if 'question' in body:
                entry['question'] = body['question'].strip()
            if 'answer' in body:
                entry['answer'] = body['answer'].strip()
            if 'category' in body:
                entry['category'] = body['category']
            if 'tags' in body:
                tags = body['tags']
                entry['tags'] = tags if isinstance(tags, list) else [t.strip() for t in tags.split(',') if t.strip()]
            entry['updated_at'] = datetime.now(timezone.utc).isoformat()
            _save_knowledge(data)
            return jsonify({'success': True, 'entry': entry})
    return jsonify({'error': 'Entry not found'}), 404


@geogpt_bp.route('/knowledge/<entry_id>', methods=['DELETE'])
def delete_knowledge(entry_id: str):
    """Delete a knowledge entry. Requires admin access."""
    username = request.args.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    data = _load_knowledge()
    entries = data.get('entries', [])
    original_count = len(entries)
    data['entries'] = [e for e in entries if e['id'] != entry_id]

    if len(data['entries']) == original_count:
        return jsonify({'error': 'Entry not found'}), 404

    _save_knowledge(data)
    return jsonify({'success': True})


# ------------------------------------------------------------------
# Chat (AI-powered with document search context)
# ------------------------------------------------------------------

_MAX_HISTORY_TURNS = 10  # Keep last N exchanges to limit token usage


@geogpt_bp.route('/chat', methods=['POST'])
def chat():
    """AI-powered chat with document search context (RAG) and conversation history."""
    body = request.get_json() or {}
    question = body.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Ingen spørsmål oppgitt'}), 400

    # Conversation history from the frontend (optional)
    history = body.get('history', [])
    # Keep only the last N turns to limit token usage
    if len(history) > _MAX_HISTORY_TURNS * 2:
        history = history[-_MAX_HISTORY_TURNS * 2:]

    # Search Azure AI Search index
    search_docs, search_error = _search_documents(question)

    # Try AI-powered response
    client = _get_ai_client()
    if client:
        # Build context from search results
        if search_docs:
            parts = ["=== DOKUMENTER ==="]
            for i, doc in enumerate(search_docs, 1):
                title   = doc.get('title') or doc.get('source', 'Ukjent')
                content = doc.get('content', '')[:2000]
                parts.append(f"[{i}] {title}\n{content}")
            context = "\n\n".join(parts)
        else:
            context = "Ingen dokumenter funnet i søkeindeksen for dette spørsmålet."

        # Build message list: system + history + current question
        messages = [
            {"role": "system", "content": f"{_SYSTEM_PROMPT}\n\n--- KONTEKST ---\n{context}"},
        ]
        # Append prior conversation turns (only role + content)
        for turn in history:
            role = turn.get('role')
            content = turn.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({"role": role, "content": content})
        # Current question (always the last user message)
        messages.append({"role": "user", "content": question})

        try:
            response = client.chat.completions.create(
                model=_DEPLOYMENT,
                messages=messages,
            )
            ai_answer = response.choices[0].message.content
            documents = []
            for doc in search_docs:
                src = doc.get('source', '')
                documents.append({
                    'title': doc.get('title') or src,
                    'source': src,
                    'download_url': f'/api/geogpt/documents/{src}/download' if src else '',
                })
            return jsonify({
                'answer': ai_answer,
                'documents': documents,
                'ai_powered': True,
                'search_error': search_error,
            })
        except Exception as exc:
            print(f'GeoGPT AI error: {exc}')
            return jsonify({
                'error': 'Kunne ikke generere svar. Sjekk AI-konfigurasjonen.',
            }), 502

    # No AI configured — return search results or helpful message
    if search_error:
        return jsonify({
            'answer': f'⚠️ {search_error}',
            'documents': [],
            'ai_powered': False,
            'search_error': search_error,
        })

    if search_docs:
        best = search_docs[0]
        return jsonify({
            'answer': best.get('content', 'Ingen innhold tilgjengelig.')[:1500],
            'documents': [{'title': best.get('title', best.get('source', '')),
                           'source': best.get('source', ''),
                           'download_url': f"/api/geogpt/documents/{best.get('source', '')}/download"}],
            'ai_powered': False,
        })

    return jsonify({
        'answer': 'Ingen dokumenter er indeksert ennå. Last opp dokumenter i Administrer-fanen og kjør indeksering.',
        'documents': [],
        'ai_powered': False,
        'search_error': search_error,
    })


# ------------------------------------------------------------------
# Document download
# ------------------------------------------------------------------

@geogpt_bp.route('/documents/<path:blob_name>/download', methods=['GET'])
def download_document(blob_name: str):
    """Generate a time-limited SAS URL and redirect to download a document."""
    sas_url = _get_blob_sas_url(blob_name)
    if not sas_url:
        # Fallback: try to serve directly from blob
        if not _BLOB_CONN_STR:
            return jsonify({'error': 'Blob storage ikke konfigurert'}), 503
        try:
            from azure.storage.blob import BlobServiceClient
            svc = BlobServiceClient.from_connection_string(_BLOB_CONN_STR)
            bc = svc.get_blob_client(container=_GEOGPT_CONTAINER, blob=blob_name)
            data = bc.download_blob().readall()
            from flask import Response
            filename = blob_name.split('/')[-1]
            return Response(
                data,
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'application/octet-stream',
                },
            )
        except Exception as exc:
            return jsonify({'error': f'Kunne ikke laste ned: {exc}'}), 404

    from flask import redirect
    return redirect(sas_url)


@geogpt_bp.route('/documents', methods=['GET'])
def list_documents():
    """List all documents in the GeoGPT blob container."""
    if not _BLOB_CONN_STR:
        return jsonify({'documents': [], 'error': 'Blob storage ikke konfigurert'})
    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(_BLOB_CONN_STR)
        container = svc.get_container_client(_GEOGPT_CONTAINER)
        blobs = []
        for b in container.list_blobs():
            blobs.append({
                'name': b.name,
                'size': b.size,
                'last_modified': b.last_modified.isoformat() if b.last_modified else None,
                'download_url': f'/api/geogpt/documents/{b.name}/download',
            })
        return jsonify({'documents': blobs})
    except Exception as exc:
        return jsonify({'documents': [], 'error': str(exc)})


@geogpt_bp.route('/documents', methods=['POST'])
def upload_document():
    """Upload a document to the GeoGPT blob container and trigger reindexing. Admin only."""
    username = request.form.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'Ingen fil i forespørselen'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Tomt filnavn'}), 400

    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    data = file.read()

    if not _BLOB_CONN_STR:
        return jsonify({'error': 'Blob storage ikke konfigurert'}), 503

    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(_BLOB_CONN_STR)
        try:
            svc.create_container(_GEOGPT_CONTAINER)
        except Exception:
            pass  # Container already exists
        bc = svc.get_blob_client(container=_GEOGPT_CONTAINER, blob=filename)
        bc.upload_blob(data, overwrite=True)
    except Exception as exc:
        return jsonify({'error': f'Opplasting feilet: {exc}'}), 500

    # Trigger indexer run if Search is configured
    indexer_triggered = False
    if _SEARCH_ENDPOINT and _SEARCH_KEY:
        try:
            from activities.geogpt.indexer import run_indexer
            run_indexer()
            indexer_triggered = True
        except Exception as exc:
            print(f'GeoGPT indexer trigger error after upload: {exc}')

    return jsonify({
        'success': True,
        'filename': filename,
        'size': len(data),
        'indexer_triggered': indexer_triggered,
    })


@geogpt_bp.route('/documents/<path:blob_name>', methods=['DELETE'])
def delete_document_blob(blob_name: str):
    """Delete a document from blob storage and remove it from the search index. Admin only."""
    username = request.args.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    if not _BLOB_CONN_STR:
        return jsonify({'error': 'Blob storage ikke konfigurert'}), 503

    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(_BLOB_CONN_STR)
        bc = svc.get_blob_client(container=_GEOGPT_CONTAINER, blob=blob_name)
        bc.delete_blob()
    except Exception as exc:
        return jsonify({'error': f'Sletting feilet: {exc}'}), 500

    # Remove from search index
    if _SEARCH_ENDPOINT and _SEARCH_KEY:
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            sc = SearchClient(
                endpoint=_SEARCH_ENDPOINT,
                index_name=_SEARCH_INDEX,
                credential=AzureKeyCredential(_SEARCH_KEY),
            )
            hits = list(sc.search(
                search_text='*',
                filter=f"metadata_storage_name eq '{blob_name}'",
                select=['id'],
            ))
            if hits:
                sc.delete_documents(documents=[{'id': r['id']} for r in hits])
        except Exception as exc:
            print(f'GeoGPT index cleanup error: {exc}')

    return jsonify({'success': True})


# ------------------------------------------------------------------
# Index management (admin)
# ------------------------------------------------------------------

@geogpt_bp.route('/index/setup', methods=['POST'])
def index_setup():
    """Create/update index, data source, and indexer in Azure AI Search. Admin only."""
    body = request.get_json() or {}
    username = body.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    if not _SEARCH_ENDPOINT or not _SEARCH_KEY:
        return jsonify({'error': 'Azure AI Search er ikke konfigurert i .env'}), 503

    if not _BLOB_CONN_STR:
        return jsonify({'error': 'Azure Blob Storage er ikke konfigurert i .env'}), 503

    # Ensure blob container exists
    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(_BLOB_CONN_STR)
        svc.create_container(_GEOGPT_CONTAINER)
    except Exception:
        pass  # Already exists

    try:
        from activities.geogpt.indexer import full_setup
        results = full_setup()
        return jsonify({'success': True, 'results': results})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@geogpt_bp.route('/index/run', methods=['POST'])
def index_run():
    """Trigger an immediate indexer run. Admin only."""
    body = request.get_json() or {}
    username = body.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    if not _SEARCH_ENDPOINT or not _SEARCH_KEY:
        return jsonify({'error': 'Azure AI Search er ikke konfigurert i .env'}), 503

    try:
        from activities.geogpt.indexer import run_indexer
        result = run_indexer()
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@geogpt_bp.route('/index/status', methods=['GET'])
def index_status():
    """Return the current indexer status. Admin only."""
    username = request.args.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    if not _SEARCH_ENDPOINT or not _SEARCH_KEY:
        return jsonify({'configured': False, 'status': 'Azure AI Search ikke konfigurert'})

    try:
        from activities.geogpt.indexer import get_indexer_status
        status = get_indexer_status()
        return jsonify({'configured': True, **status})
    except Exception as exc:
        return jsonify({'configured': True, 'error': str(exc)})


@geogpt_bp.route('/search-debug', methods=['GET'])
def search_debug():
    """Admin-only: test search with a query and return raw results."""
    username = request.args.get('username', '')
    if not _is_admin(username):
        return jsonify({'error': 'Ingen admin-tilgang'}), 403

    q = request.args.get('q', 'test')
    docs, error = _search_documents(q, top=3)
    return jsonify({
        'query': q,
        'endpoint': _SEARCH_ENDPOINT,
        'index': _SEARCH_INDEX,
        'results_count': len(docs),
        'error': error,
        'results': docs,
    })


# ------------------------------------------------------------------
# Admin check
# ------------------------------------------------------------------

@geogpt_bp.route('/admin-check', methods=['GET'])
def admin_check():
    """Check if a user has admin access to GeoGPT."""
    username = request.args.get('username', '')
    return jsonify({'is_admin': _is_admin(username)})


@geogpt_bp.route('/debug', methods=['GET'])
def debug_info():
    """Debug endpoint — shows GeoGPT configuration status."""
    return jsonify({
        'azure_openai_configured': bool(_AZURE_ENDPOINT and _AZURE_KEY),
        'azure_search_configured': bool(_SEARCH_ENDPOINT and _SEARCH_KEY),
        'search_index': _SEARCH_INDEX,
        'deployment': _DEPLOYMENT,
        'blob_configured': bool(_BLOB_CONN_STR),
        'knowledge_file_exists': os.path.exists(_KNOWLEDGE_FILE),
    })
