# -*- coding: utf-8 -*-
"""
Frontend Configuration
=======================
All frontend-side configuration constants: backend URL, page titles,
and other settings used across pages and components.
"""

import os

# URL of the Flask backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5050")

# Application title shown in the browser tab and sidebar
APP_TITLE = "RamGAP"

# Default request timeout in seconds
REQUEST_TIMEOUT = 5
