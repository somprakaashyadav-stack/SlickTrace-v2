import sys
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_endpoint(name, method, url, json=None, expected_status=200):
    try:
        print(f"Testing {name} ({method} {url})... ", end="")
        if method == "GET":
            response = client.get(url)
        elif method == "POST":
            response = client.post(url, json=json)
        
        if response.status_code == expected_status:
            print("PASS")
            return True, response.json()
        else:
            print(f"FAIL (Status: {response.status_code}, {response.text})")
            return False, None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def run_all_tests():
    spill_id = "spill-123"
    print("--- STARTING SLICKTRACE V2 END-TO-END TEST ---")
    
    # 1. Satellite Status
    test_endpoint("Satellite Status", "GET", "/api/satellite/status")
    
    # 2. Detection (Spill Polygon generation)
    # The default spill_id in detection route mock might not be 'spill-123' if it's dynamic, but let's try.
    # Actually, we can just POST without payload as it defaults to S1B...
    success, res = test_endpoint("Oil Spill Detection", "POST", "/api/detection/run", json={})
    if success and res:
        spill_id = res.get("spill_id", "spill-123")
    
    # 3. Characterization
    test_endpoint("Slick Characterization", "POST", f"/api/characterization/{spill_id}")
    
    # 4. Drift Simulation (Backward)
    drift_payload = {
        "spill_id": spill_id,
        "hours_modeled": 12,
        "mode": "backward"
    }
    test_endpoint("Drift Simulation (Hindcast)", "POST", "/api/drift/simulate", json=drift_payload)
    
    # 5. Origin Cone
    test_endpoint("4D Origin Cone", "GET", f"/api/origin/{spill_id}")
    
    # 7. Anomaly Detection
    # Since we need an MMSI, we can grab it from the AIS Correlation response
    mmsi = 123456789
    success, ais_res = test_endpoint("AIS Correlation", "POST", f"/api/ais/correlate/{spill_id}")
    if success and ais_res and ais_res.get("candidates"):
        mmsi = ais_res["candidates"][0].get("mmsi", mmsi)
        
    test_endpoint("Anomaly Detection", "POST", f"/api/anomaly/analyze/{spill_id}/{mmsi}")
    
    # 8. Initial Scoring
    test_endpoint("Initial Suspect Scoring", "POST", f"/api/scoring/initial/{spill_id}")
    
    # 9. Physics Verification
    test_endpoint("Counterfactual Physics Verification", "POST", f"/api/physics_verification/run/{spill_id}?top_n=3")
    
    # 10. Final Ranking
    test_endpoint("Final Suspect Ranking", "GET", f"/api/ranking/{spill_id}")
    
    # 11. PDF Report Generation
    test_endpoint("PDF Report Generation", "POST", f"/api/report/generate/{spill_id}")
    
    print("--- END OF TEST ---")

if __name__ == "__main__":
    run_all_tests()
