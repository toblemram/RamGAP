# -*- coding: utf-8 -*-
"""
Custom Exceptions
=================
Application-specific exception classes.
Raise these instead of generic exceptions so callers can handle error
types explicitly and return consistent API error responses.
"""


class RamGAPError(Exception):
    """Base exception for all RamGAP errors."""


class PlaxisConnectionError(RamGAPError):
    """Raised when a connection to the Plaxis server fails."""


class PlaxisNotAvailableError(RamGAPError):
    """Raised when plxscripting is not installed or Plaxis is not running."""


class ParseError(RamGAPError):
    """Raised when a geotechnical file cannot be parsed."""


class ProjectNotFoundError(RamGAPError):
    """Raised when a requested project does not exist."""
