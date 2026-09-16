import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_anomaly_ocean_titan():
    # 419001234 is MV Ocean Titan, which has a gap and speed drop in our mock data
    res = client.post("/api/anomaly/analyze/test-spill/419001234")
    assert res.status_code == 200
    data = res.json()
    
    assert data["mmsi"] == 419001234
    assert "speed_details" in data
    assert "gap_details" in data
    
    print(f"Ocean Titan Anomaly Result:")
    print(f"  Overall Flag: {data['overall_anomaly_flag']}")
    print(f"  Speed Score: {data['speed_anomaly_score']}")
    print(f"  Gap Details: {data['gap_details']['classification']} - {data['gap_details']['reason']}")
    print(f"  Isolation Forest Score: {data['trajectory_anomaly_score']}")

def test_anomaly_innocent_vessel():
    # 419009876 is CSCL Star Voyager, innocent transit
    res = client.post("/api/anomaly/analyze/test-spill/419009876")
    assert res.status_code == 200
    data = res.json()
    
    print(f"\nStar Voyager Anomaly Result:")
    print(f"  Overall Flag: {data['overall_anomaly_flag']}")
    print(f"  Gap Details: {data['gap_details']['classification']} - {data['gap_details']['reason']}")
