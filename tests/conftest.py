# -*- coding: utf-8 -*-
"""
Pytest Fixtures
===============
Shared fixtures available to all tests in the suite.
Add fixtures here that are needed by both unit and integration tests.
"""

import pytest
from backend.app import app as flask_app


@pytest.fixture()
def app():
    """Create a Flask test application instance."""
    flask_app.config.update({"TESTING": True})
    yield flask_app


@pytest.fixture()
def client(app):
    """Create a Flask test client."""
    return app.test_client()
