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


class APIClient:
    """Thin wrapper around requests for the RamGAP backend."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip('/')

    def _get(self, path: str, params: dict = None, timeout: int = None) -> dict:
        try:
            r = requests.get(f'{self.base_url}{path}', params=params, timeout=timeout)
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def _post(self, path: str, payload: dict = None, timeout: int = None) -> dict:
        try:
            r = requests.post(f'{self.base_url}{path}', json=payload, timeout=timeout)
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def _delete(self, path: str, params: dict = None, timeout: int = None) -> dict:
        try:
            r = requests.delete(f'{self.base_url}{path}', params=params, timeout=timeout)
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def _put(self, path: str, payload: dict = None, timeout: int = None) -> dict:
        try:
            r = requests.put(f'{self.base_url}{path}', json=payload, timeout=timeout)
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def is_healthy(self) -> bool:
        """Return True if the backend responds to the health check."""
        try:
            r = requests.get(f'{self.base_url}/api/health', timeout=1)
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
                       created_by: str, allowed_users: List[str],
                       folder_path: str = '') -> dict:
        return self._post('/api/projects', {
            'name': name, 'description': description,
            'created_by': created_by, 'allowed_users': allowed_users,
            'folder_path': folder_path,
        })

    def delete_project(self, project_id: int, username: str, confirm: str) -> dict:
        return self._delete(f'/api/projects/{project_id}',
                            {'username': username, 'confirm': confirm})

    def update_project(self, project_id: int, username: str,
                       name: str = None, description: str = None,
                       project_owner: str = None,
                       folder_path: str = None) -> dict:
        payload: Dict[str, Any] = {'username': username}
        if name is not None:
            payload['name'] = name
        if description is not None:
            payload['description'] = description
        if project_owner is not None:
            payload['project_owner'] = project_owner
        if folder_path is not None:
            payload['folder_path'] = folder_path
        return self._put(f'/api/projects/{project_id}', payload)

    def add_project_access(self, project_id: int,
                            username: str,
                            granted_by: str) -> dict:
        return self._post(
            f'/api/projects/{project_id}/access',
            {'username': username, 'granted_by': granted_by},
        )

    def remove_project_access(self, project_id: int,
                               username_to_remove: str,
                               requesting_user: str) -> dict:
        return self._delete(
            f'/api/projects/{project_id}/access/{username_to_remove}',
            {'username': requesting_user},
        )

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

    def plaxis_parametric_run(self, payload: dict) -> dict:
        return self._post('/api/plaxis/parametric-run', payload, timeout=120)

    def plaxis_water_sensitivity_run(self, payload: dict) -> dict:
        return self._post('/api/plaxis/water-sensitivity-run', payload, timeout=120)

    def plaxis_ai_quality_check(self, model_data: dict) -> dict:
        return self._post('/api/plaxis/ai-quality-check', {'model_data': model_data}, timeout=60)

    def plaxis_ai_report(self, payload: dict) -> dict:
        return self._post('/api/plaxis/ai-report', payload, timeout=60)

    def get_plaxis_calculations(self, project_id: Optional[int] = None,
                                 limit: int = 10) -> List[dict]:
        params = {'limit': limit}
        if project_id:
            params['project_id'] = project_id
        result = self._get('/api/plaxis/calculations', params)
        return result.get('calculations', [])

    def save_plaxis_calculation(self, payload: dict) -> dict:
        return self._post('/api/plaxis/calculations', payload, timeout=30)

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
                                    parsed_data: dict, layers: list,
                                    has_oedometer: bool = False,
                                    snd_raw_content: str = None) -> dict:
        return self._post(f'/api/geotolk/sessions/{session_id}/interpretations', {
            'filename': filename,
            'parsed_data': parsed_data,
            'layers': layers,
            'has_oedometer': has_oedometer,
            'snd_raw_content': snd_raw_content,
        })

    def complete_geotolk_session(self, session_id: int, files: list,
                                  username: str) -> dict:
        """Complete a GeoTolk session: store ML training data and log activity."""
        return self._post(f'/api/geotolk/sessions/{session_id}/complete', {
            'files': files,
            'username': username,
        }, timeout=120)

    def get_geotolk_project_sessions(self, project_id: int, limit: int = 20) -> list:
        """Get completed GeoTolk sessions for a project."""
        result = self._get('/api/geotolk/project-sessions',
                           {'project_id': project_id, 'limit': limit})
        return result.get('sessions', [])

    def get_geotolk_session_resume(self, session_id: int) -> dict:
        """Get full session data (with parsed arrays + raw content) for resuming."""
        return self._get(f'/api/geotolk/sessions/{session_id}/resume', timeout=30)

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

    # ------------------------------------------------------------------
    # Tørmur V220
    # ------------------------------------------------------------------

    def save_tormur_params(self, activity_id: int, params: dict) -> dict:
        return self._post(
            f'/api/modeling/activities/{activity_id}/tormur-params', params
        )

    def get_tormur_params(self, activity_id: int) -> dict:
        return self._get(
            f'/api/modeling/activities/{activity_id}/tormur-params'
        )

    def tormur_check(self, params: dict) -> dict:
        return self._post('/api/modeling/tormur/check', params)

    def optimize_tormur(self, activity_id: int, params: dict,
                         sections: list, bt_range: list = None,
                         bb_range: list = None,
                         smooth_window: int = 3) -> dict:
        payload = {
            'params': params,
            'sections': sections,
            'smooth_window': smooth_window,
        }
        if bt_range:
            payload['bt_range'] = bt_range
        if bb_range:
            payload['bb_range'] = bb_range
        return self._post(
            f'/api/modeling/activities/{activity_id}/optimize',
            payload, timeout=120,
        )

    def get_modeling_excel_export_url(self, activity_id: int) -> str:
        """Return the URL for downloading the Excel export."""
        return f'{self.base_url}/api/modeling/activities/{activity_id}/export/excel'

    # ------------------------------------------------------------------
    # Plaxis Agent
    # ------------------------------------------------------------------

    def plaxis_agent_chat(self, message: str, session_id: str = 'default',
                          history: list = None, pdf_text: str = None,
                          auto_execute: bool = False,
                          selected_context: list = None) -> dict:
        return self._post('/api/plaxis-agent/chat', {
            'message': message,
            'session_id': session_id,
            'history': history,
            'pdf_text': pdf_text,
            'auto_execute': auto_execute,
            'selected_context': selected_context,
        }, timeout=120)

    def plaxis_agent_execute(self, code: str, session_id: str = 'default') -> dict:
        return self._post('/api/plaxis-agent/execute', {
            'code': code,
            'session_id': session_id,
        }, timeout=60)

    def plaxis_agent_upload_pdf(self, file_bytes: bytes, filename: str) -> dict:
        try:
            r = requests.post(
                f'{self.base_url}/api/plaxis-agent/upload-pdf',
                files={'file': (filename, file_bytes, 'application/pdf')},
                timeout=30,
            )
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def plaxis_agent_status(self) -> dict:
        return self._get('/api/plaxis-agent/status', timeout=10)

    def plaxis_agent_connect(self, port: int, password: str,
                              session_id: str = 'default',
                              output_port: int = None,
                              output_password: str = None) -> dict:
        return self._post('/api/plaxis-agent/connect', {
            'port': port,
            'password': password,
            'session_id': session_id,
            'output_port': output_port,
            'output_password': output_password,
        }, timeout=15)

    # ------------------------------------------------------------------
    # Standarder
    # ------------------------------------------------------------------

    def upload_standard(self, file_bytes: bytes, filename: str,
                        name: str = '') -> dict:
        try:
            r = requests.post(
                f'{self.base_url}/api/standarder/upload',
                files={'file': (filename, file_bytes, 'application/pdf')},
                data={'name': name} if name else {},
                timeout=120,
            )
            return r.json() if r.ok else {'error': r.text}
        except requests.RequestException as exc:
            return {'error': str(exc)}

    def get_standards(self) -> list:
        result = self._get('/api/standarder/documents')
        return result.get('documents', [])

    def delete_standard(self, doc_id: str) -> dict:
        return self._delete(f'/api/standarder/documents/{doc_id}')

    def get_standard_sections(self, doc_id: str) -> list:
        result = self._get(f'/api/standarder/documents/{doc_id}/sections')
        return result.get('sections', [])

    def search_standards(self, query: str, doc_id: str = '') -> list:
        params: dict = {'q': query}
        if doc_id:
            params['doc_id'] = doc_id
        result = self._get('/api/standarder/search', params=params)
        return result.get('results', [])

    def check_standard_compliance(self, doc_id: str, project_summary: str,
                                   section_ids: list = None) -> dict:
        return self._post('/api/standarder/check', {
            'doc_id': doc_id,
            'project_summary': project_summary,
            'section_ids': section_ids or [],
        }, timeout=120)

    def explain_standard_section(self, doc_id: str, section_id: str,
                                  project_context: str = '') -> dict:
        return self._post('/api/standarder/explain', {
            'doc_id': doc_id,
            'section_id': section_id,
            'project_context': project_context,
        }, timeout=60)

    def reparse_standard(self, doc_id: str) -> dict:
        return self._post(f'/api/standarder/documents/{doc_id}/reparse',
                          timeout=120)

    def extract_report_text(self, file_path: str) -> dict:
        return self._post('/api/standarder/extract-report', {
            'file_path': file_path,
        }, timeout=60)
