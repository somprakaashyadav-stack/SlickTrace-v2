import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_ais_correlation():
    res = client.post("/api/ais/correlate/test-spill-id")
    assert res.status_code == 200
    data = res.json()
    assert "spill_id" in data
    assert "candidates" in data
    assert len(data["candidates"]) > 0
    
    top_candidate = data["candidates"][0]
    assert "scores" in top_candidate
    assert top_candidate["candidate_status"] in ["High Risk", "Medium Risk", "Low Risk", "Irrelevant"]
    assert "spatial_score" in top_candidate["scores"]
    
    print(f"Found {len(data['candidates'])} candidates. Top candidate: {top_candidate['vessel_name']} (Total Score: {top_candidate['scores']['total_score']})")
