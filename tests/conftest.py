# -*- coding: utf-8 -*-
"""
Pytest Fixtures
===============
Delte fixtures tilgjengelig for alle tester i test-suiten.
"""

import pytest
from backend.app import app as flask_app


# ---------------------------------------------------------------------------
# Flask-fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """Lag en Flask-testapplikasjon."""
    flask_app.config.update({"TESTING": True})
    yield flask_app


@pytest.fixture()
def client(app):
    """Lag en Flask-testklient."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Live Plaxis CLI-argumenter
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--plaxis-port",
        action="store",
        default=None,
        help="Plaxis Input server port (f.eks. 10000)",
    )
    parser.addoption(
        "--plaxis-password",
        action="store",
        default=None,
        help="Plaxis Input server passord",
    )
    parser.addoption(
        "--plaxis-out-port",
        action="store",
        default=None,
        help="Plaxis Output server port (valgfri — hvis ikke gitt åpnes Output via g_i.view())",
    )


@pytest.fixture(scope="session")
def plaxis_connection(request):
    """
    Live Plaxis-tilkobling for integrasjonstester.
    Hoppes over automatisk hvis --plaxis-port og --plaxis-password ikke er oppgitt.

    Bruk:
        pytest tests/ --plaxis-port 10000 --plaxis-password DittPassord
        pytest tests/ --plaxis-port 10000 --plaxis-password Pass --plaxis-out-port 10001
    """
    port     = request.config.getoption("--plaxis-port")
    password = request.config.getoption("--plaxis-password")
    out_port = request.config.getoption("--plaxis-out-port")

    if not port or not password:
        pytest.skip("Oppgi --plaxis-port og --plaxis-password for å kjøre live Plaxis-tester")

    try:
        from plxscripting.easy import new_server
    except ImportError:
        pytest.skip("plxscripting ikke tilgjengelig i dette miljøet")

    s_i, g_i = new_server("localhost", int(port), password=password)

    if out_port:
        s_o, g_o = new_server("localhost", int(out_port), password=password)
    else:
        view_port = g_i.view(g_i.Phases[0])
        s_o, g_o  = new_server("localhost", view_port, password=password)

    return {
        "s_i":      s_i,
        "g_i":      g_i,
        "s_o":      s_o,
        "g_o":      g_o,
        "port":     int(port),
        "password": password,
        "out_port": int(out_port) if out_port else None,
    }
