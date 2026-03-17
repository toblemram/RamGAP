# -*- coding: utf-8 -*-
"""
Plaxis Service Module for RamGAP
Handles connection to Plaxis and extraction of model data
"""

import json
from typing import Dict, List, Optional, Any

# Try to import plxscripting - will fail if not installed
try:
    from plxscripting.easy import new_server
    PLAXIS_AVAILABLE = True
except ImportError:
    PLAXIS_AVAILABLE = False


class PlaxisService:
    """Service class for Plaxis operations"""
    
    def __init__(self):
        self.s_i = None  # Input server
        self.g_i = None  # Input geometry
        self.s_o = None  # Output server
        self.g_o = None  # Output geometry
        self.port = None
        self.password = None
        self.connected = False
        
    def connect(self, port: int, password: str) -> Dict[str, Any]:
        """
        Connect to Plaxis Input server
        Returns connection status and any error message
        """
        if not PLAXIS_AVAILABLE:
            return {
                'success': False,
                'error': 'plxscripting module not available. Run this from Plaxis Python environment.'
            }
        
        try:
            self.s_i, self.g_i = new_server('localhost', port, password=password)
            self.port = port
            self.password = password
            self.connected = True
            return {
                'success': True,
                'message': 'Connected to Plaxis successfully'
            }
        except Exception as e:
            self.connected = False
            return {
                'success': False,
                'error': str(e)
            }
    
    def disconnect(self):
        """Disconnect from Plaxis"""
        self.s_i = None
        self.g_i = None
        self.s_o = None
        self.g_o = None
        self.connected = False
    
    def extract_model_info(self) -> Dict[str, Any]:
        """
        Extract all structures and phases from the Plaxis model
        Equivalent to level1 function in existing code
        """
        if not self.connected or not self.g_i:
            return {'error': 'Not connected to Plaxis'}
        
        try:
            # Initialize structure lists
            structures = {
                'plates': [],
                'embedded_beams': [],
                'node_to_node_anchors': [],
                'fixed_end_anchors': [],
                'geogrids': []
            }
            
            # Go to structures mode
            self.g_i.gotostructures()
            
            # Extract Plates
            if hasattr(self.g_i, 'Plates'):
                for plate in self.g_i.Plates:
                    structures['plates'].append({
                        'name': plate.Name.value,
                        'display_name': f"Name: {plate.Name.value}, x = {plate.Parent.First.x.value}",
                        'x': plate.Parent.First.x.value,
                        'type': 'plate'
                    })
            
            # Extract Embedded Beam Rows
            if hasattr(self.g_i, 'EmbeddedBeamRows'):
                for ebr in self.g_i.EmbeddedBeamRows:
                    structures['embedded_beams'].append({
                        'name': ebr.Name.value,
                        'display_name': f"Name: {ebr.Name.value}, x = {ebr.Parent.First.x.value}",
                        'x': ebr.Parent.First.x.value,
                        'type': 'embedded_beam'
                    })
            
            # Extract Node to Node Anchors
            if hasattr(self.g_i, 'NodeToNodeAnchors'):
                for n2n in self.g_i.NodeToNodeAnchors:
                    structures['node_to_node_anchors'].append({
                        'name': n2n.Name.value,
                        'display_name': f"Name: {n2n.Name.value}, ({n2n.Parent.First.x.value},{n2n.Parent.First.y.value}) → ({n2n.Parent.Second.x.value},{n2n.Parent.Second.y.value})",
                        'x1': n2n.Parent.First.x.value,
                        'y1': n2n.Parent.First.y.value,
                        'x2': n2n.Parent.Second.x.value,
                        'y2': n2n.Parent.Second.y.value,
                        'type': 'node_to_node_anchor'
                    })
            
            # Extract Fixed End Anchors
            if hasattr(self.g_i, 'FixedEndAnchors'):
                for fea in self.g_i.FixedEndAnchors:
                    structures['fixed_end_anchors'].append({
                        'name': fea.Name.value,
                        'display_name': f"Name: {fea.Name.value}, ({fea.Parent.x.value},{fea.Parent.y.value})",
                        'x': fea.Parent.x.value,
                        'y': fea.Parent.y.value,
                        'type': 'fixed_end_anchor'
                    })
            
            # Extract Geogrids
            if hasattr(self.g_i, 'Geogrids'):
                for geo in self.g_i.Geogrids:
                    structures['geogrids'].append({
                        'name': geo.Name.value,
                        'display_name': f"Name: {geo.Name.value}, ({geo.Parent.First.x.value},{geo.Parent.First.y.value}) → ({geo.Parent.Second.x.value},{geo.Parent.Second.y.value})",
                        'x1': geo.Parent.First.x.value,
                        'y1': geo.Parent.First.y.value,
                        'x2': geo.Parent.Second.x.value,
                        'y2': geo.Parent.Second.y.value,
                        'type': 'geogrid'
                    })
            
            # Extract Phases
            self.g_i.gotostages()
            phase_names = self.g_i.Phases.Identification.value
            
            phases = []
            for i, name in enumerate(phase_names):
                phases.append({
                    'id': i,
                    'name': name,
                    'msf_enabled': False,
                    'ux_enabled': False,
                    'capacity_enabled': False
                })
            
            return {
                'success': True,
                'structures': structures,
                'phases': phases
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_anchors_for_spunt(self, spunt_x: float, tolerance: float = 0.1) -> Dict[str, List]:
        """
        Find all anchors that connect to a spunt at given x-coordinate
        """
        if not self.connected or not self.g_i:
            return {'error': 'Not connected to Plaxis'}
        
        anchors = {
            'node_to_node_anchors': [],
            'fixed_end_anchors': []
        }
        
        try:
            self.g_i.gotostructures()
            
            # Find N2N anchors at this x
            if hasattr(self.g_i, 'NodeToNodeAnchors'):
                for n2n in self.g_i.NodeToNodeAnchors:
                    x1 = n2n.Parent.First.x.value
                    x2 = n2n.Parent.Second.x.value
                    if abs(x1 - spunt_x) < tolerance or abs(x2 - spunt_x) < tolerance:
                        anchors['node_to_node_anchors'].append({
                            'name': n2n.Name.value,
                            'x1': x1,
                            'y1': n2n.Parent.First.y.value,
                            'x2': x2,
                            'y2': n2n.Parent.Second.y.value
                        })
            
            # Find Fixed End Anchors at this x
            if hasattr(self.g_i, 'FixedEndAnchors'):
                for fea in self.g_i.FixedEndAnchors:
                    x = fea.Parent.x.value
                    if abs(x - spunt_x) < tolerance:
                        anchors['fixed_end_anchors'].append({
                            'name': fea.Name.value,
                            'x': x,
                            'y': fea.Parent.y.value
                        })
            
            return {
                'success': True,
                'anchors': anchors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Global service instance
plaxis_service = PlaxisService()


def get_plaxis_service() -> PlaxisService:
    """Get the global Plaxis service instance"""
    return plaxis_service
