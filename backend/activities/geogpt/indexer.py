# -*- coding: utf-8 -*-
"""
GeoGPT — Azure AI Search index management
==========================================
Handles programmatic creation and management of the Azure AI Search index,
data source connector, and indexer for GeoGPT documents.

Usage:
    from activities.geogpt.indexer import full_setup, run_indexer, get_indexer_status
"""

import os

_SEARCH_ENDPOINT  = os.getenv('AZURE_SEARCH_ENDPOINT', '')
_SEARCH_KEY       = os.getenv('AZURE_SEARCH_KEY', '')
_SEARCH_INDEX     = os.getenv('AZURE_SEARCH_INDEX', 'geogpt-knowledge')
_BLOB_CONN_STR    = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
_GEOGPT_CONTAINER = os.getenv('GEOGPT_BLOB_CONTAINER', 'geogpt-knowledge')

_DATASOURCE_NAME = 'geogpt-blob'
_INDEXER_NAME    = 'geogpt-indexer'


def _cred():
    from azure.core.credentials import AzureKeyCredential
    return AzureKeyCredential(_SEARCH_KEY)


def setup_index() -> dict:
    """Create or update the Azure AI Search index with the GeoGPT schema."""
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

    # Try with semantic search first; fall back without if tier doesn't support it
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
                continue  # retry without semantic
            raise exc


def setup_datasource() -> dict:
    """Create or update the blob storage data source connection."""
    from azure.search.documents.indexes import SearchIndexerClient
    from azure.search.documents.indexes.models import (
        SearchIndexerDataSourceConnection, SearchIndexerDataContainer,
    )

    datasource = SearchIndexerDataSourceConnection(
        name=_DATASOURCE_NAME,
        type='azureblob',
        connection_string=_BLOB_CONN_STR,
        container=SearchIndexerDataContainer(name=_GEOGPT_CONTAINER),
    )
    client = SearchIndexerClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
    result = client.create_or_update_data_source_connection(datasource)
    return {'success': True, 'name': result.name}


def setup_indexer() -> dict:
    """Create or update the blob indexer (runs every 2 hours automatically)."""
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
        schedule=IndexingSchedule(interval='PT2H'),
    )
    client = SearchIndexerClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
    result = client.create_or_update_indexer(indexer)
    return {'success': True, 'name': result.name}


def run_indexer() -> dict:
    """Trigger an immediate indexer run."""
    from azure.search.documents.indexes import SearchIndexerClient
    client = SearchIndexerClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
    client.run_indexer(_INDEXER_NAME)
    return {'success': True, 'message': 'Indexer kjøres nå'}


def get_indexer_status() -> dict:
    """Return current status of the GeoGPT indexer."""
    from azure.search.documents.indexes import SearchIndexerClient
    client = SearchIndexerClient(endpoint=_SEARCH_ENDPOINT, credential=_cred())
    try:
        status = client.get_indexer_status(_INDEXER_NAME)
        last_run = status.last_result
        return {
            'status': status.status.value if status.status else 'ukjent',
            'last_run_status': last_run.status.value if last_run and last_run.status else None,
            'last_run_time': last_run.end_time.isoformat() if last_run and last_run.end_time else None,
            'documents_succeeded': last_run.item_count if last_run else 0,
            'errors': len(last_run.errors) if last_run and last_run.errors else 0,
        }
    except Exception as exc:
        return {'status': 'ikke satt opp', 'error': str(exc)}


def full_setup() -> dict:
    """One-shot: create index + datasource + indexer, then trigger immediate run."""
    results = {}
    results['index']      = setup_index()
    results['datasource'] = setup_datasource()
    results['indexer']    = setup_indexer()
    results['run']        = run_indexer()
    return results
