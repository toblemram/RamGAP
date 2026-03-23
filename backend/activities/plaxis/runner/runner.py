# -*- coding: utf-8 -*-
"""
Plaxis Extraction Runner
========================
Orchestrates a complete Plaxis result-extraction job:
  1. Connect to Plaxis Input and Output servers
  2. Resolve structures and phases
  3. Run capacity, MSF, and/or displacement extraction
  4. Write results to Excel

Public API:
    run_plaxis_extraction(input_port, input_password, job, ...) -> dict
    build_job_from_frontend(...)                                 -> dict
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from plxscripting.easy import new_server
    PLAXIS_AVAILABLE = True
except ImportError:
    new_server = None  # type: ignore[assignment]
    PLAXIS_AVAILABLE = False

from activities.plaxis.extraction.result_extractor import run_capacity, run_msf, run_displacement
from activities.plaxis.extraction.structure_resolver import resolve_structures, resolve_phases
from activities.plaxis.extraction.excel_exporter import print_results_to_excel


def run_plaxis_extraction(
    input_port: int,
    input_password: str,
    job: Dict[str, Any],
    output_port: Optional[int] = None,
    output_password: Optional[str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> Dict[str, Any]:
    """
    Run the complete Plaxis extraction workflow.

    Args:
        input_port:         Plaxis Input server port.
        input_password:     Plaxis Input server password.
        job:                Job configuration dict. Expected keys:
                              structures, analysis, resultsPath.
        output_port:        Plaxis Output server port (optional).
                            If omitted the runner opens Output via ``g_i.view()``.
        output_password:    Plaxis Output password (defaults to input_password).
        progress_callback:  Optional ``callback(percent: int, message: str)``.

    Returns:
        Dict with keys: success, capacity, msf, displacement, output_file, errors.
    """
    if not PLAXIS_AVAILABLE:
        return {
            'success': False,
            'error': 'plxscripting is not available. Run from the Plaxis Python environment.',
        }

    results: Dict[str, Any] = {
        'success': False,
        'capacity': {},
        'msf': {},
        'displacement': {},
        'output_file': None,
        'errors': [],
    }

    def _progress(pct: int, msg: str) -> None:
        if progress_callback:
            progress_callback(pct, msg)

    try:
        _progress(5, 'Connecting to Plaxis Input...')
        s_i, g_i = new_server('localhost', input_port, password=input_password)

        _progress(10, 'Connecting to Plaxis Output...')
        if output_port and output_password:
            s_o, g_o = new_server('localhost', output_port, password=output_password)
        else:
            port_out = g_i.view(g_i.Phases[0])
            pwd_out  = output_password or input_password
            s_o, g_o = new_server('localhost', port_out, password=pwd_out)

        _progress(20, 'Resolving structures...')
        selected_structures = resolve_structures(g_o, job)

        analysis = job.get('analysis', {})

        # Capacity check
        if analysis.get('capacity_check', {}).get('enabled'):
            _progress(30, 'Extracting structural forces...')
            phases = resolve_phases(g_o, analysis['capacity_check']['phases'])
            results['capacity'] = run_capacity(g_o, selected_structures, phases)

        # MSF safety factor
        if analysis.get('msf', {}).get('enabled'):
            _progress(50, 'Extracting MSF values...')
            phases = resolve_phases(g_o, analysis['msf']['phases'])
            results['msf'] = run_msf(g_o, phases)

        # Displacement
        if analysis.get('displacement', {}).get('enabled'):
            _progress(70, 'Extracting displacement data...')
            phases    = resolve_phases(g_o, analysis['displacement']['phases'])
            component = analysis['displacement'].get('component', 'Ux')
            results['displacement'] = run_displacement(g_o, selected_structures, phases, component)

        # Export to Excel
        _progress(85, 'Writing Excel output...')
        output_file = print_results_to_excel(results, job)
        results['output_file'] = str(output_file)

        _progress(100, 'Done!')
        results['success'] = True

    except Exception as exc:  # noqa: BLE001
        results['errors'].append(str(exc))
        results['success'] = False

    return results


def build_job_from_frontend(
    selected_spunts: List[str],
    selected_anchors: List[str],
    selected_phases: Dict[str, Dict[str, bool]],
    output_path: str,
    model_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Translate frontend selections into a job configuration dict.

    Args:
        selected_spunts:   Names of selected plates / embedded beams.
        selected_anchors:  Names of selected anchor elements.
        selected_phases:   {phase_name: {msf, ux, capacity}} booleans.
        output_path:       Folder path for Excel output.
        model_data:        Model info dict returned by the Plaxis routes.

    Returns:
        A job dict ready for ``run_plaxis_extraction``.
    """
    structures = model_data.get('structures', {})

    job_structures: Dict[str, List[str]] = {
        'plates': [], 'embedded_beams': [],
        'node_to_node_anchors': [], 'fixed_end_anchors': [], 'geogrids': [],
    }

    for name in selected_spunts:
        for plate in structures.get('plates', []):
            if plate['name'] == name:
                job_structures['plates'].append(name)
        for eb in structures.get('embedded_beams', []):
            if eb['name'] == name:
                job_structures['embedded_beams'].append(name)

    for name in selected_anchors:
        for n2n in structures.get('node_to_node_anchors', []):
            if n2n['name'] == name:
                job_structures['node_to_node_anchors'].append(name)
        for fea in structures.get('fixed_end_anchors', []):
            if fea['name'] == name:
                job_structures['fixed_end_anchors'].append(name)

    capacity_phases    = [p for p, sel in selected_phases.items() if sel.get('capacity')]
    msf_phases         = [p for p, sel in selected_phases.items() if sel.get('msf')]
    displacement_phases = [p for p, sel in selected_phases.items() if sel.get('ux')]

    return {
        'structures': job_structures,
        'analysis': {
            'capacity_check': {
                'enabled': bool(capacity_phases),
                'phases':   capacity_phases,
            },
            'msf': {
                'enabled': bool(msf_phases),
                'phases':   msf_phases,
            },
            'displacement': {
                'enabled':   bool(displacement_phases),
                'phases':    displacement_phases,
                'component': 'Ux',
            },
        },
        'resultsPath': {'path': output_path},
    }
