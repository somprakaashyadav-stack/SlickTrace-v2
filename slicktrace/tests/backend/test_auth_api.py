"""
Tests for SlickTrace v2 Authentication Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_login_success():
    # Investigator login
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator@agency.gov", "password": "secure_password", "remember_me": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "Investigator"
    assert data["email"] == "investigator@agency.gov"
    assert data["mode"] == "real"

    # Analyst login
    resp2 = client.post(
        "/api/v1/auth/login",
        json={"email": "marine.analyst@agency.gov", "password": "secure_password"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["role"] == "Analyst"

    # Admin login
    resp3 = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@agency.gov", "password": "secure_password"},
    )
    assert resp3.status_code == 200
    assert resp3.json()["role"] == "Administrator"


def test_auth_login_invalid_credentials():
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator@agency.gov", "password": "wrong"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authentication failed. Verify credentials and try again."


def test_auth_demo_endpoint():
    resp = client.post("/api/v1/auth/demo", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "demo"
    assert "access_token" in data
    assert "Sandbox" in data["role"]
