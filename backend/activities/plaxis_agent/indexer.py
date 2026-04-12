# -*- coding: utf-8 -*-
"""
GAPI — Azure AI Search index for PLAXIS manual
================================================
Handles creation and management of a dedicated Azure AI Search index,
blob data source, and indexer for the PLAXIS 2D Tutorial Manual (PDF).

Mirrors the GeoGPT indexer pattern but uses a separate index and container
so that PLAXIS manual content is isolated from geotechnical standards.

Usage:
    from activities.plaxis_agent.indexer import (
        full_setup, run_indexer, get_indexer_status, search_manual,
        upload_manual_blob,
    )
"""

import os

_SEARCH_ENDPOINT  = os.getenv('AZURE_SEARCH_ENDPOINT', '')
_SEARCH_KEY       = os.getenv('AZURE_SEARCH_KEY', '')
_SEARCH_INDEX     = os.getenv('GAPI_SEARCH_INDEX', 'gapi-plaxis-manual')
_BLOB_CONN_STR    = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
_BLOB_CONTAINER   = os.getenv('GAPI_BLOB_CONTAINER', 'gapi-plaxis-manual')

_DATASOURCE_NAME = 'gapi-plaxis-blob'
_INDEXER_NAME    = 'gapi-plaxis-indexer'


def _cred():
    from azure.core.credentials import AzureKeyCredential
    return AzureKeyCredential(_SEARCH_KEY)


# ---------------------------------------------------------------------------
# Index setup
# ---------------------------------------------------------------------------

def setup_index() -> dict:
    """Create or update the Azure AI Search index for the PLAXIS manual."""
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex, SimpleField, SearchableField, SearchFieldDataType,
        SemanticConfiguration, SemanticSearch,
        SemanticPrioritizedFields, SemanticField,
    )

    fields = [
        SimpleField(name='id', type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name='content', type=SearchFieldDataType.String),
        SearchableField(name='title', type=SearchFieldDataType.String, filterable=True, retrievable=True),
        SimpleField(name='source', type=SearchFieldDataType.String, filterable=True, retrievable=True),
        SimpleField(name='metadata_storage_name', type=SearchFieldDataType.String, filterable=True, retrievable=True),
        SimpleField(name='metadata_storage_path', type=SearchFieldDataType.String, retrievable=True),
        SimpleField(name='metadata_storage_size', type=SearchFieldDataType.Int64, retrievable=True),
        SimpleField(name='metadata_storage_last_modified', type=SearchFieldDataType.DateTimeOffset, retrievable=True),
        SimpleField(name='metadata_storage_content_type', type=SearchFieldDataType.String, retrievable=True),
    ]

    semantic_config = SemanticConfiguration(
        name='default',
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[SemanticField(field_name='content')],
            title_field=SemanticField(field_name='title'),
        ),
    )

    for use_semantic in (True, False):
        kwargs = {}
        if use_semantic:
            kwargs['semantic_search'] = SemanticSearch(configurations=[semantic_config])
        index = SearchIndex(name=_SEARCH_INDEX, fields=fields, **kwargs)
        try:
            client = SearchIndexClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
            result = client.create_or_update_index(index)
            return {'success': True, 'name': result.name, 'semantic': use_semantic}
        except Exception as exc:
            if use_semantic:
                continue
            raise exc


def setup_datasource() -> dict:
    """Create or update the blob storage data source for the PLAXIS manual."""
    from azure.search.documents.indexes import SearchIndexerClient
    from azure.search.documents.indexes.models import (
        SearchIndexerDataSourceConnection, SearchIndexerDataContainer,
    )

    datasource = SearchIndexerDataSourceConnection(
        name=_DATASOURCE_NAME,
        type='azureblob',
        connection_string=_BLOB_CONN_STR,
        container=SearchIndexerDataContainer(name=_BLOB_CONTAINER),
    )
    client = SearchIndexerClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
    result = client.create_or_update_data_source_connection(datasource)
    return {'success': True, 'name': result.name}


def setup_indexer() -> dict:
    """Create or update the blob indexer for the PLAXIS manual (runs every 24h)."""
    from azure.search.documents.indexes import SearchIndexerClient
    from azure.search.documents.indexes.models import (
        SearchIndexer, IndexingSchedule, FieldMapping, FieldMappingFunction,
    )

    indexer = SearchIndexer(
        name=_INDEXER_NAME,
        data_source_name=_DATASOURCE_NAME,
        target_index_name=_SEARCH_INDEX,
        field_mappings=[
            FieldMapping(
                source_field_name='metadata_storage_path',
                target_field_name='id',
                mapping_function=FieldMappingFunction(name='base64Encode'),
            ),
            FieldMapping(
                source_field_name='metadata_storage_name',
                target_field_name='source',
            ),
        ],
        schedule=IndexingSchedule(interval='PT24H'),
    )
    client = SearchIndexerClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
    result = client.create_or_update_indexer(indexer)
    return {'success': True, 'name': result.name}


def run_indexer() -> dict:
    """Trigger an immediate indexer run."""
    from azure.search.documents.indexes import SearchIndexerClient
    client = SearchIndexerClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
    client.run_indexer(_INDEXER_NAME)
    return {'success': True, 'message': 'PLAXIS manual-indekserer kjøres nå'}


def get_indexer_status() -> dict:
    """Return current status of the PLAXIS manual indexer."""
    from azure.search.documents.indexes import SearchIndexerClient
    client = SearchIndexerClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
    try:
        status = client.get_indexer_status(_INDEXER_NAME)
        last_run = status.last_result

        def _val(v):
            """Handle both enum and string values from Azure SDK."""
            if v is None:
                return None
            return v.value if hasattr(v, 'value') else str(v)

        return {
            'status': _val(status.status) or 'ukjent',
            'last_run_status': _val(last_run.status) if last_run else None,
            'last_run_time': last_run.end_time.isoformat() if last_run and last_run.end_time else None,
            'documents_succeeded': last_run.item_count if last_run else 0,
            'errors': len(last_run.errors) if last_run and last_run.errors else 0,
        }
    except Exception as exc:
        return {'status': 'ikke satt opp', 'error': str(exc)}


def full_setup() -> dict:
    """One-shot: create index + datasource + indexer, then trigger run."""
    results = {}
    results['index']      = setup_index()
    results['datasource'] = setup_datasource()
    results['indexer']    = setup_indexer()
    results['run']        = run_indexer()
    return results


# ---------------------------------------------------------------------------
# Blob operations
# ---------------------------------------------------------------------------

def upload_manual_blob(filename: str, data: bytes) -> dict:
    """Upload a file (PDF) to the PLAXIS manual blob container."""
    if not _BLOB_CONN_STR:
        raise RuntimeError('Azure Blob Storage er ikke konfigurert (AZURE_STORAGE_CONNECTION_STRING)')

    from azure.storage.blob import BlobServiceClient
    svc = BlobServiceClient.from_connection_string(_BLOB_CONN_STR)
    try:
        svc.create_container(_BLOB_CONTAINER)
    except Exception:
        pass  # Already exists

    bc = svc.get_blob_client(container=_BLOB_CONTAINER, blob=filename)
    bc.upload_blob(data, overwrite=True)
    return {'success': True, 'filename': filename, 'size': len(data)}


def list_manual_blobs() -> list[dict]:
    """List all blobs in the PLAXIS manual container."""
    if not _BLOB_CONN_STR:
        return []
    try:
        from azure.storage.blob import BlobServiceClient
        svc = BlobServiceClient.from_connection_string(_BLOB_CONN_STR)
        container = svc.get_container_client(_BLOB_CONTAINER)
        return [
            {
                'name': b.name,
                'size': b.size,
                'last_modified': b.last_modified.isoformat() if b.last_modified else None,
            }
            for b in container.list_blobs()
        ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Search — query the indexed PLAXIS manual
# ---------------------------------------------------------------------------

def search_manual(query: str, top: int = 5) -> tuple[list[dict], str | None]:
    """
    Search the PLAXIS manual index.

    Returns (docs, error_message).
    Each doc: {"content": str, "title": str, "source": str, "score": float}
    """
    if not _SEARCH_ENDPOINT or not _SEARCH_KEY:
        return [], 'Azure AI Search er ikke konfigurert'

    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        client = SearchClient(
            endpoint=_SEARCH_ENDPOINT,
            index_name=_SEARCH_INDEX,
            credential=AzureKeyCredential(_SEARCH_KEY),
        )
    except Exception as exc:
        return [], f'Kunne ikke opprette søkeklient: {exc}'

    def _parse(results) -> list[dict]:
        docs = []
        for r in results:
            source = r.get('source') or r.get('metadata_storage_name', '')
            title = r.get('title') or source
            docs.append({
                'content': r.get('content', ''),
                'title': title,
                'source': source,
                'score': r.get('@search.reranker_score') or r.get('@search.score', 0),
            })
        return docs

    for query_type, extra in [
        ('semantic', {'semantic_configuration_name': 'default'}),
        ('simple',   {}),
    ]:
        try:
            results = client.search(
                search_text=query,
                top=top,
                query_type=query_type,
                **extra,
            )
            return _parse(results), None
        except Exception as exc:
            if query_type == 'semantic':
                continue
            return [], f'Søk feilet: {str(exc)[:200]}'

    return [], 'Søk feilet etter alle forsøk'
