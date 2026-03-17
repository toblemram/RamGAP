# -*- coding: utf-8 -*-
"""
Created on Tue Feb 24 21:13:48 2026

@author: KIAA
"""

from plxscripting.easy import *

def level1(port, passord):

    # ---------------------------------
    # Connect to PLAXIS Input
    # ---------------------------------
    plx_server = 'localhost'
    s_i, g_i = new_server(plx_server, port, password=passord)

    # ---------------------------------
    # STRUCTURES
    # ---------------------------------

    Plates_name = []
    Plates_structkallenavn = []

    EmbeddedBeamRow_name = []
    EmbeddedBeamRow_structkallenavn = []

    n2nA_name = []
    n2nA_structkallenavn = []
    
    # Fixed-End Anchors
    FEA_name = []
    FEA_structkallenavn = []
    
    # Geogrids
    Geogrid_name = []
    Geogrid_structkallenavn = []

    g_i.gotostructures()
    
    # ---- Plates ----
    if hasattr(g_i, 'Plates'):
        for plate in g_i.Plates:
            Plates_name.append(plate.Name.value)
            Plates_structkallenavn.append(
                f"Name: {plate.Name.value}, x = {plate.Parent.First.x.value}"
            )

    # ---- Embedded Beam Rows ----
    if hasattr(g_i, 'EmbeddedBeamRows'):
        for ebr in g_i.EmbeddedBeamRows:
            EmbeddedBeamRow_name.append(ebr.Name.value)
            EmbeddedBeamRow_structkallenavn.append(
                f"Name: {ebr.Name.value}, x = {ebr.Parent.First.x.value}"
            )

    # ---- Node to Node Anchors ----
    if hasattr(g_i, 'NodeToNodeAnchors'):
        for n2n in g_i.NodeToNodeAnchors:
            n2nA_name.append(n2n.Name.value)
            n2nA_structkallenavn.append(
                f"Name: {n2n.Name.value}, "
                f"({n2n.Parent.First.x.value},{n2n.Parent.First.y.value}) → "
                f"({n2n.Parent.Second.x.value},{n2n.Parent.Second.y.value})"
            )

    # ---- Fixed-End Anchors ----
    if hasattr(g_i, 'FixedEndAnchors'):
        for fea in g_i.FixedEndAnchors:
            FEA_name.append(fea.Name.value)
            FEA_structkallenavn.append(
                f"Name: {fea.Name.value}, "
                f"({fea.Parent.x.value},{fea.Parent.y.value})"
            )

    # ---- Geogrids ----
    if hasattr(g_i, 'Geogrids'):
        for geo in g_i.Geogrids:
            Geogrid_name.append(geo.Name.value)
            Geogrid_structkallenavn.append(
                f"Name: {geo.Name.value}, "
                f"({geo.Parent.First.x.value},{geo.Parent.First.y.value}) → "
                f"({geo.Parent.Second.x.value},{geo.Parent.Second.y.value})"
            )
    
    
    
    # ---------------------------------
    # PHASES
    # ---------------------------------
  
    g_i.gotostages()
    phase_names = g_i.Phases.Identification.value

    # ---------------------------------
    # RETURN
    # ---------------------------------

    return {
        "plates": {
            "names": Plates_name,
            "structkallenavn": Plates_structkallenavn
        },
        "embedded_beams": {
            "names": EmbeddedBeamRow_name,
            "structkallenavn": EmbeddedBeamRow_structkallenavn
        },
        "node_to_node_anchors": {
            "names": n2nA_name,
            "structkallenavn": n2nA_structkallenavn
        },
        "fixed_end_anchors": {
            "names": FEA_name,
            "structkallenavn": FEA_structkallenavn
        },
        "geogrids": {
            "names": Geogrid_name,
            "structkallenavn": Geogrid_structkallenavn
        },
        "phases": phase_names
    }