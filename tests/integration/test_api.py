# -*- coding: utf-8 -*-
"""
Integration Tests — Flask API
================================
End-to-end tests for the REST API endpoints using Flask's test client.
The database is initialised in-memory for each test session.
"""

import pytest


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_create_and_list_project(client):
    payload = {
        "name": "Test Project",
        "description": "Integration test",
        "created_by": "test_user",
        "allowed_users": [],
    }
    create_resp = client.post("/api/projects", json=payload)
    assert create_resp.status_code == 201

    list_resp = client.get("/api/projects", query_string={"username": "test_user"})
    assert list_resp.status_code == 200
    projects = list_resp.get_json()["projects"]
    assert any(p["name"] == "Test Project" for p in projects)
