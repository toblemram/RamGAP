# -*- coding: utf-8 -*-
"""
Frontend API Client
====================
All HTTP calls to the Flask backend are centralised here.
Import from this module instead of calling ``requests`` directly in pages.

Usage:
    from components.api_client import APIClient
    api = APIClient()
    projects = api.get_projects(username)
"""

import os
import requests
from typing import Any, Dict, List, Optional

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5050')
_API_KEY = os.getenv('API_KEY', '')


class APIClient:
    """Thin wrapper around requests for the RamGAP backend."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip('/')
        self._headers = {'X-API-Key': _API_KEY} if _API_KEY else {}

    def _get(self, path: str, params: dict = None, timeout: int = None) -> dict:
        try:
            r = requests.get(f'{self.base_url}{path}', params=params,
                             headers=self._headers, timeout=timeout)
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def _post(self, path: str, payload: dict = None, timeout: int = None) -> dict:
        try:
            r = requests.post(f'{self.base_url}{path}', json=payload,
                              headers=self._headers, timeout=timeout)
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def _delete(self, path: str, params: dict = None, timeout: int = None) -> dict:
        try:
            r = requests.delete(f'{self.base_url}{path}', params=params,
                                headers=self._headers, timeout=timeout)
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def is_healthy(self) -> bool:
        """Return True if the backend responds to the health check."""
        try:
            r = requests.get(f'{self.base_url}/api/health',
                             headers=self._headers, timeout=1)
            return r.status_code == 200
        except requests.RequestException:
            return False

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def get_projects(self, username: str) -> List[dict]:
        result = self._get('/api/projects', {'username': username})
        return result.get('projects', [])

    def create_project(self, name: str, description: str,
                       created_by: str, allowed_users: List[str]) -> dict:
        return self._post('/api/projects', {
            'name': name, 'description': description,
            'created_by': created_by, 'allowed_users': allowed_users,
        })

    def delete_project(self, project_id: int, username: str) -> dict:
        return self._delete(f'/api/projects/{project_id}', {'username': username})

    # ------------------------------------------------------------------
    # Activity log
    # ------------------------------------------------------------------

    def get_recent_activity(self, username: str, limit: int = 5) -> List[dict]:
        result = self._get('/api/activity', {'username': username, 'limit': limit})
        return result.get('activities', [])

    def log_activity(self, username: str, activity_type: str, activity_name: str) -> None:
        self._post('/api/activity', {
            'username': username,
            'activity_type': activity_type,
            'activity_name': activity_name,
        })

    def log_project_activity(self, project_id: int, username: str,
                              activity_type: str, activity_name: str) -> None:
        self._post(f'/api/projects/{project_id}/activities', {
            'username': username,
            'activity_type': activity_type,
            'activity_name': activity_name,
        })

    def get_project_activities(self, project_id: int, limit: int = 10) -> List[dict]:
        result = self._get(f'/api/projects/{project_id}/activities', {'limit': limit})
        return result.get('activities', [])

    # ------------------------------------------------------------------
    # Plaxis
    # ------------------------------------------------------------------

    def plaxis_connect(self, port: int, password: str, session_id: str) -> dict:
        return self._post('/api/plaxis/connect', {
            'port': port, 'password': password, 'session_id': session_id,
        }, timeout=10)

    def plaxis_model_info(self, session_id: str) -> dict:
        return self._get('/api/plaxis/model-info', {'session_id': session_id}, timeout=30)

    def plaxis_run(self, payload: dict) -> dict:
        return self._post('/api/plaxis/run', payload, timeout=300)

    def get_plaxis_calculations(self, project_id: Optional[int] = None,
                                 limit: int = 10) -> List[dict]:
        params = {'limit': limit}
        if project_id:
            params['project_id'] = project_id
        result = self._get('/api/plaxis/calculations', params)
        return result.get('calculations', [])

    def rerun_plaxis_calculation(self, calc_id: int, input_password: str,
                                  output_password: str = None,
                                  session_id: str = 'default') -> dict:
        return self._post(f'/api/plaxis/calculations/{calc_id}/rerun', {
            'session_id': session_id,
            'input_password': input_password,
            'output_password': output_password or input_password,
        }, timeout=300)

    # ------------------------------------------------------------------
    # GeoTolk
    # ------------------------------------------------------------------

    def geotolk_parse(self, content: str) -> dict:
        return self._post('/api/geotolk/parse', {'content': content}, timeout=10)

    def create_geotolk_session(self, project_id: Optional[int],
                                activity_name: str, username: str) -> dict:
        return self._post('/api/geotolk/sessions', {
            'project_id': project_id,
            'activity_name': activity_name,
            'username': username,
        })

    def add_geotolk_interpretation(self, session_id: int, filename: str,
                                    parsed_data: dict, layers: list) -> dict:
        return self._post(f'/api/geotolk/sessions/{session_id}/interpretations', {
            'filename': filename,
            'parsed_data': parsed_data,
            'layers': layers,
        })

    # ------------------------------------------------------------------
    # Modeling
    # ------------------------------------------------------------------

    def get_modeling_activities(self, project_id: int) -> List[dict]:
        result = self._get('/api/modeling/activities', {'project_id': project_id})
        return result.get('activities', [])

    def create_modeling_activity(self, project_id: int, name: str,
                                  username: str) -> dict:
        return self._post('/api/modeling/activities', {
            'project_id': project_id,
            'name': name,
            'username': username,
        })

    def delete_modeling_activity(self, activity_id: int) -> dict:
        try:
            r = requests.delete(
                f'{self.base_url}/api/modeling/activities/{activity_id}',
                timeout=10,
            )
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def upload_modeling_excel(self, activity_id: int,
                               file_bytes: bytes, filename: str) -> dict:
        try:
            r = requests.post(
                f'{self.base_url}/api/modeling/activities/{activity_id}/upload/excel',
                files={'file': (filename, file_bytes,
                                'application/vnd.openxmlformats-officedocument'
                                '.spreadsheetml.sheet')},
                timeout=60,
            )
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def upload_modeling_results(self, activity_id: int,
                                 report_bytes: bytes,
                                 summary_bytes: bytes = None,
                                 ifc_bytes: bytes = None,
                                 ifc_filename: str = 'model.ifc') -> dict:
        files: dict = {
            'report': ('run-report.json', report_bytes, 'application/json'),
        }
        if summary_bytes:
            files['summary'] = ('run-summary.md', summary_bytes, 'text/markdown')
        if ifc_bytes:
            files['ifc'] = (ifc_filename, ifc_bytes, 'application/octet-stream')
        try:
            r = requests.post(
                f'{self.base_url}/api/modeling/activities/{activity_id}/upload/results',
                files=files,
                timeout=120,
            )
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def get_modeling_results(self, activity_id: int) -> dict:
        return self._get(f'/api/modeling/activities/{activity_id}/results')

    def get_modeling_download_url(self, activity_id: int,
                                   file_type: str) -> dict:
        """file_type: 'excel' or 'ifc'"""
        return self._get(
            f'/api/modeling/activities/{activity_id}/download/{file_type}'
        )
