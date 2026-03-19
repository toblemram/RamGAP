# -*- coding: utf-8 -*-
"""
Unit Tests — Plaxis Service
============================
Tests for the PlaxisService class.
plxscripting is mocked so no live Plaxis instance is needed.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture()
def service():
    """Return a PlaxisService with plxscripting mocked out."""
    with patch("plaxis.plaxis_service.PLAXIS_AVAILABLE", True), \
         patch("plaxis.plaxis_service.new_server") as mock_ns:
        mock_ns.return_value = (MagicMock(), MagicMock())
        from plaxis.plaxis_service import PlaxisService
        yield PlaxisService()


def test_connect_success(service):
    result = service.connect(10000, "test-password")
    assert result["success"] is True


def test_connect_sets_connected_flag(service):
    service.connect(10000, "test-password")
    assert service.connected is True
