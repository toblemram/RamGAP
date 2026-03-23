# -*- coding: utf-8 -*-
"""
Blob Storage Service — Modeling Activity
=========================================
Thin wrapper around azure-storage-blob for the modeling activity module.
Handles upload, download and SAS-URL generation for Excel and IFC files.
"""

import os
from datetime import datetime, timedelta, timezone

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    ContentSettings,
    generate_blob_sas,
)

_CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER', 'project-files')


def _client() -> BlobServiceClient:
    conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
    if not conn_str:
        raise RuntimeError('AZURE_STORAGE_CONNECTION_STRING is not configured.')
    return BlobServiceClient.from_connection_string(conn_str)


def upload_file(blob_name: str, data: bytes,
                content_type: str = 'application/octet-stream') -> str:
    """Upload bytes to Blob Storage. Returns the blob name."""
    bc = _client().get_blob_client(container=_CONTAINER, blob=blob_name)
    bc.upload_blob(data, overwrite=True,
                   content_settings=ContentSettings(content_type=content_type))
    return blob_name


def download_file(blob_name: str) -> bytes:
    """Download and return bytes for a blob."""
    bc = _client().get_blob_client(container=_CONTAINER, blob=blob_name)
    return bc.download_blob().readall()


def get_sas_url(blob_name: str, expiry_hours: int = 1) -> str:
    """Return a time-limited SAS URL for direct client download."""
    svc = _client()
    sas = generate_blob_sas(
        account_name=svc.account_name,
        container_name=_CONTAINER,
        blob_name=blob_name,
        account_key=svc.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
    )
    return (
        f'https://{svc.account_name}.blob.core.windows.net'
        f'/{_CONTAINER}/{blob_name}?{sas}'
    )


def blob_name_excel(project_id: int, activity_id: int, filename: str) -> str:
    return f'projects/{project_id}/modeling/{activity_id}/excel/{filename}'


def blob_name_ifc(project_id: int, activity_id: int, filename: str) -> str:
    return f'projects/{project_id}/modeling/{activity_id}/ifc/{filename}'
