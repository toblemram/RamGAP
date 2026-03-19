# -*- coding: utf-8 -*-
"""
Created on Tue Feb 24 21:13:48 2026

@author: KIAA
"""

from plxscripting.easy import *
from level5_extractPlaxisResults import *
from level5_printResults import *

    # ---------------------------------
    # STRUCTURES
    # ---------------------------------

def resolve_structures(g_o, job):
    """
    Converts structure names from job config into actual PLAXIS objects.
    Returns dictionary with resolved objects.
    """

#   g_i.gotostructures()
    
    selected = {}

    structure_map = {
        "plates": "Plates",
        "embedded_beams": "EmbeddedBeamRows",
        "node_to_node_anchors": "NodeToNodeAnchors",
        "fixed_end_anchors": "FixedEndAnchors",
        "geogrids": "Geogrids"
    }

    for job_key, plaxis_attr in structure_map.items():       

        selected[job_key] = []
        selected_names = job["structures"][job_key]

        # Skip if user selected none of this type
        if not selected_names:
            continue

        # Skip if structure type does not exist in model
        if not hasattr(g_o, plaxis_attr):
            continue

        plaxis_objects = getattr(g_o, plaxis_attr)

        

        for obj in plaxis_objects:
            if obj.Name.value in selected_names:
                selected[job_key].append(obj)

    return selected

    # ---------------------------------
    # PHASES
    # ---------------------------------

def resolve_phases(g_o, phase_names):
    """
   Resolves Output phase objects by matching the START
   of the Identification string.

   Example:
       Input name:  "SLS Excavation"
       Output name: "SLS Excavation [Phase_3]"
   """

    resolved = []

    for phase in g_o.Phases:
       phase_id = phase.Identification.value

       for target_name in phase_names:
           if phase_id.startswith(target_name):
               resolved.append(phase)
               break  # avoid duplicates

    return resolved


def level5(port, passord, data):

    # ---------------------------------
    # Connect to PLAXIS Input
    # ---------------------------------
    plx_server = 'localhost'
    s_i, g_i = new_server(plx_server, port, password=passord)


    # ---------------------------------
    # Connect to PLAXIS Output
    # ---------------------------------

    
    port_output = g_i.view(g_i.Phases[0])                                           #Åpne output og sette opp server
    s_o, g_o=new_server(plx_server,port_output,password = passord )

    # ---------------------------------
    # STRUCTURES
    # ---------------------------------

    selected_structures = resolve_structures(g_o, data)

    results = {}    

    if data["analysis"]["capacity_check"]["enabled"]:
        phases = resolve_phases(
            g_o,
            data["analysis"]["capacity_check"]["phases"]
        )
        results["capacity"] = run_capacity(g_o,selected_structures, phases)

    if data["analysis"]["msf"]["enabled"]:
        phases = resolve_phases(
            g_o,
            data["analysis"]["msf"]["phases"]
        )
        results["msf"] = run_msf(g_o, phases)

    if data["analysis"]["displacement"]["enabled"]:
        phases = resolve_phases(
            g_o,
            data["analysis"]["displacement"]["phases"]
        )
        component = data["analysis"]["displacement"]["component"]
        results["displacement"] = run_displacement(g_o,selected_structures, phases,component)

    # ---------------------------------
    # Print results
    # ---------------------------------
    
    print_results_to_excel(results, data)


    return results

