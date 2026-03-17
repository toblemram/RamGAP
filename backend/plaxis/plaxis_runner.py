# -*- coding: utf-8 -*-
"""
Plaxis Runner for RamGAP
Orchestrates the extraction of Plaxis results and Excel generation
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add plaxis module path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from plxscripting.easy import new_server
    PLAXIS_AVAILABLE = True
except ImportError:
    PLAXIS_AVAILABLE = False


def run_plaxis_extraction(
    input_port: int,
    input_password: str,
    job: Dict[str, Any],
    output_port: Optional[int] = None,
    output_password: Optional[str] = None,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Run the complete Plaxis extraction workflow.
    
    Args:
        input_port: Plaxis Input server port
        input_password: Plaxis Input server password
        output_port: Plaxis Output server port (optional, will auto-open if not provided)
        output_password: Plaxis Output server password (optional, uses input_password if not provided)
        job: Job configuration containing:
            - structures: Dict of structure lists to analyze
            - analysis: Dict of analysis types (capacity_check, msf, displacement)
            - resultsPath: Dict with 'path' key for output folder
        progress_callback: Optional function to report progress (0-100)
    
    Returns:
        Dict with results and status
    """
    
    if not PLAXIS_AVAILABLE:
        return {
            'success': False,
            'error': 'plxscripting not available. Run from Plaxis Python environment.'
        }
    
    results = {
        'success': False,
        'capacity': {},
        'msf': {},
        'displacement': {},
        'output_file': None,
        'errors': []
    }
    
    try:
        # Report progress
        if progress_callback:
            progress_callback(5, "Kobler til Plaxis Input...")
        
        # Connect to Plaxis Input
        plx_server = 'localhost'
        s_i, g_i = new_server(plx_server, input_port, password=input_password)
        
        if progress_callback:
            progress_callback(10, "Kobler til Plaxis Output...")
        
        # Connect to Plaxis Output
        # Use provided output port/password, or fall back to auto-open
        if output_port and output_password:
            # Direct connection to already-open Output
            s_o, g_o = new_server(plx_server, output_port, password=output_password)
        else:
            # Auto-open Output from Input
            port_output = g_i.view(g_i.Phases[0])
            pwd = output_password if output_password else input_password
            s_o, g_o = new_server(plx_server, port_output, password=pwd)
        
        if progress_callback:
            progress_callback(20, "Henter strukturer...")
        
        # Import extraction functions
        from .level5_extractPlaxisResults import (
            run_capacity, run_msf, run_displacement
        )
        from .level5_getData import resolve_structures, resolve_phases
        from .level5_printResults_simple import print_results_to_excel
        
        # Resolve structures
        selected_structures = resolve_structures(g_o, job)
        
        # Run capacity check
        if job.get("analysis", {}).get("capacity_check", {}).get("enabled"):
            if progress_callback:
                progress_callback(30, "Henter tverrsnittskrefter...")
            
            phases = resolve_phases(
                g_o,
                job["analysis"]["capacity_check"]["phases"]
            )
            results["capacity"] = run_capacity(g_o, selected_structures, phases)
        
        # Run MSF extraction
        if job.get("analysis", {}).get("msf", {}).get("enabled"):
            if progress_callback:
                progress_callback(50, "Henter Msf-verdier...")
            
            phases = resolve_phases(
                g_o,
                job["analysis"]["msf"]["phases"]
            )
            results["msf"] = run_msf(g_o, phases)
        
        # Run displacement extraction
        if job.get("analysis", {}).get("displacement", {}).get("enabled"):
            if progress_callback:
                progress_callback(70, "Henter deformasjonsdata...")
            
            phases = resolve_phases(
                g_o,
                job["analysis"]["displacement"]["phases"]
            )
            component = job["analysis"]["displacement"].get("component", "Ux")
            results["displacement"] = run_displacement(
                g_o, selected_structures, phases, component
            )
        
        # Generate Excel output
        if progress_callback:
            progress_callback(85, "Genererer Excel-resultater...")
        
        output_file = print_results_to_excel(results, job)
        results["output_file"] = str(output_file)
        
        if progress_callback:
            progress_callback(100, "Ferdig!")
        
        results["success"] = True
        
    except Exception as e:
        results["errors"].append(str(e))
        results["success"] = False
    
    return results


def build_job_from_frontend(
    selected_spunts: List[str],
    selected_anchors: List[str],
    selected_phases: Dict[str, Dict[str, bool]],
    output_path: str,
    model_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build a job configuration from frontend selections.
    
    Args:
        selected_spunts: List of selected spunt names
        selected_anchors: List of selected anchor names
        selected_phases: Dict mapping phase names to analysis selections
        output_path: Path to save results
        model_data: Model data from Plaxis
    
    Returns:
        Job configuration dict ready for run_plaxis_extraction
    """
    
    structures = model_data.get('structures', {})
    
    # Map selected names to structure categories
    job_structures = {
        "plates": [],
        "embedded_beams": [],
        "node_to_node_anchors": [],
        "fixed_end_anchors": [],
        "geogrids": []
    }
    
    # Add selected spunts (plates or embedded beams)
    for spunt_name in selected_spunts:
        for plate in structures.get('plates', []):
            if plate['name'] == spunt_name:
                job_structures['plates'].append(spunt_name)
        for eb in structures.get('embedded_beams', []):
            if eb['name'] == spunt_name:
                job_structures['embedded_beams'].append(spunt_name)
    
    # Add selected anchors
    for anchor_name in selected_anchors:
        for n2n in structures.get('node_to_node_anchors', []):
            if n2n['name'] == anchor_name:
                job_structures['node_to_node_anchors'].append(anchor_name)
        for fea in structures.get('fixed_end_anchors', []):
            if fea['name'] == anchor_name:
                job_structures['fixed_end_anchors'].append(anchor_name)
    
    # Build analysis config from phase selections
    capacity_phases = []
    msf_phases = []
    displacement_phases = []
    
    for phase_name, selections in selected_phases.items():
        if selections.get('capacity'):
            capacity_phases.append(phase_name)
        if selections.get('msf'):
            msf_phases.append(phase_name)
        if selections.get('ux'):
            displacement_phases.append(phase_name)
    
    job = {
        "structures": job_structures,
        "analysis": {
            "capacity_check": {
                "enabled": len(capacity_phases) > 0,
                "phases": capacity_phases
            },
            "msf": {
                "enabled": len(msf_phases) > 0,
                "phases": msf_phases
            },
            "displacement": {
                "enabled": len(displacement_phases) > 0,
                "phases": displacement_phases,
                "component": "Ux"
            }
        },
        "resultsPath": {
            "path": output_path
        }
    }
    
    return job
