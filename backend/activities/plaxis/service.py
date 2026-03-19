# -*- coding: utf-8 -*-
"""
Plaxis Service
==============
Business logic for connecting to Plaxis and reading model information.
This class is the single point of contact between the routes layer and
the plxscripting library — routes never call plxscripting directly.

Usage:
    service = PlaxisService()
    result  = service.connect(10000, 'password')
    if result['success']:
        info = service.extract_model_info()
"""

from typing import Any, Dict, List

try:
    from plxscripting.easy import new_server
    PLAXIS_AVAILABLE = True
except ImportError:
    PLAXIS_AVAILABLE = False

from activities.plaxis.extraction.level1_info import extract_model_info


class PlaxisService:
    """Maintains a Plaxis connection and exposes high-level operations."""

    def __init__(self) -> None:
        self.s_i = None       # Input server object
        self.g_i = None       # Input geometry object
        self.s_o = None       # Output server object
        self.g_o = None       # Output geometry object
        self.port: int | None = None
        self.password: str | None = None
        self.connected: bool = False

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self, port: int, password: str) -> Dict[str, Any]:
        """
        Connect to a running Plaxis Input server.

        Returns:
            {'success': True} or {'success': False, 'error': '...'}
        """
        if not PLAXIS_AVAILABLE:
            return {
                'success': False,
                'error': 'plxscripting is not available. Run from the Plaxis Python environment.',
            }
        try:
            self.s_i, self.g_i = new_server('localhost', port, password=password)
            self.port      = port
            self.password  = password
            self.connected = True
            return {'success': True, 'message': 'Connected to Plaxis successfully.'}
        except Exception as exc:
            self.connected = False
            return {'success': False, 'error': str(exc)}

    def disconnect(self) -> None:
        """Release all server references."""
        self.s_i = self.g_i = self.s_o = self.g_o = None
        self.connected = False

    # ------------------------------------------------------------------
    # Model info
    # ------------------------------------------------------------------

    def extract_model_info(self) -> Dict[str, Any]:
        """
        Read all structural elements and phase names from the open model.

        Returns:
            {'success': True, 'structures': {...}, 'phases': [...]}
            or {'success': False, 'error': '...'}
        """
        if not self.connected or not self.g_i:
            return {'success': False, 'error': 'Not connected to Plaxis.'}
        try:
            info = extract_model_info(self.g_i)
            info['success'] = True
            return info
        except Exception as exc:
            return {'success': False, 'error': str(exc)}

    def find_anchors_for_element(
        self, element_x: float, tolerance: float = 0.1
    ) -> Dict[str, Any]:
        """
        Find all anchors whose endpoint is within *tolerance* metres of
        a structural element at *element_x*.

        Returns:
            {'node_to_node_anchors': [...], 'fixed_end_anchors': [...]}
        """
        if not self.connected or not self.g_i:
            return {'error': 'Not connected to Plaxis.'}

        anchors: Dict[str, List] = {'node_to_node_anchors': [], 'fixed_end_anchors': []}

        try:
            self.g_i.gotostructures()

            if hasattr(self.g_i, 'NodeToNodeAnchors'):
                for n2n in self.g_i.NodeToNodeAnchors:
                    x1 = n2n.Parent.First.x.value
                    x2 = n2n.Parent.Second.x.value
                    if abs(x1 - element_x) < tolerance or abs(x2 - element_x) < tolerance:
                        anchors['node_to_node_anchors'].append({
                            'name': n2n.Name.value,
                            'x1': x1, 'y1': n2n.Parent.First.y.value,
                            'x2': x2, 'y2': n2n.Parent.Second.y.value,
                        })

            if hasattr(self.g_i, 'FixedEndAnchors'):
                for fea in self.g_i.FixedEndAnchors:
                    x = fea.Parent.x.value
                    if abs(x - element_x) < tolerance:
                        anchors['fixed_end_anchors'].append({
                            'name': fea.Name.value,
                            'x': x, 'y': fea.Parent.y.value,
                        })
        except Exception as exc:
            return {'error': str(exc)}

        return anchors

