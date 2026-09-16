import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_drift_hindcast():
    res = client.post("/api/drift/simulate", json={"spill_id": "test", "hours_modeled": 12, "mode": "backward"})
    assert res.status_code == 200
    data = res.json()
    assert data["engine"] == "Demo Lagrangian Model"
    assert data["direction"] == "backward"
    assert data["particle_count"] == 50
    assert "origin_candidate" in data
    assert data["origin_candidate"]["X0"] is not None
    assert len(data["trajectories"]) == 50
    assert len(data["trajectories"][0]) == 13 # 0 to 12

def test_drift_forecast():
    res = client.post("/api/drift/simulate", json={"spill_id": "test", "hours_modeled": 6, "mode": "forward"})
    assert res.status_code == 200
    data = res.json()
    assert data["direction"] == "forward"
    assert "origin_candidate" not in data or data["origin_candidate"] is None
