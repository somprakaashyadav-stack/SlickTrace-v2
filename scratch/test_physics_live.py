import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_physics_verification_engine():
    res = client.post("/api/physics_verification/run/test-spill?top_n=3")
    assert res.status_code == 200
    data = res.json()
    
    assert data["spill_id"] == "test-spill"
    assert data["top_n_tested"] == 3
    assert len(data["results"]) > 0
    
    top_result = data["results"][0]
    
    print("\n--- PHYSICS VERIFICATION BEST MATCH ---")
    print(f"Vessel: {top_result['vessel_name']}")
    print(f"Physics Consistency Score: {top_result['physics_consistency_score']}")
    print(f"Classification: {top_result['classification']}")
    
    metrics = top_result['metrics']
    print("Metrics:")
    print(f"  Spatial Overlap: {metrics['spatial_overlap_pct']:.1f}%")
    print(f"  Centroid Error: {metrics['centroid_error_km']:.2f} km")
    print(f"  Shape Similarity: {metrics['shape_similarity_score']:.1f}")
    print(f"  Orientation Similarity: {metrics['orientation_similarity_score']:.1f}")
    print(f"  Timing Error: {metrics['timing_error_hours']:.1f} hrs")
    
    scenario = top_result['best_scenario']
    print(f"Best Scenario Release: {scenario['release_lat']:.4f}, {scenario['release_lon']:.4f} at {scenario['release_time']}")

    # Ensure forbidden terms aren't in classification
    forbidden = ["guilty", "caused", "responsible"]
    for term in forbidden:
        assert term not in top_result['classification'].lower()
