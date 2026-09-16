import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_characterization_flow():
    # Run detection first to put it in cache
    res = client.post("/api/detection/run", json={"scene_id": "test", "model_architecture": "U-Net", "confidence_threshold": 0.85})
    assert res.status_code == 200
    spill_id = res.json()["spill_id"]
    
    # Run characterization
    res_char = client.post(f"/api/characterization/{spill_id}")
    assert res_char.status_code == 200
    data = res_char.json()
    
    assert "area_km2" in data
    assert "elongation_ratio" in data
    assert "estimated_age_hours" in data
    
    print("Characterization response:", data)
