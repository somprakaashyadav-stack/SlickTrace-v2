import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_final_ranking_engine():
    res = client.get("/api/ranking/test-spill")
    assert res.status_code == 200
    data = res.json()
    
    assert data["spill_id"] == "test-spill"
    assert "alpha_weight" in data
    assert "beta_weight" in data
    assert len(data["rankings"]) > 0
    
    top_result = data["rankings"][0]
    
    print("\n--- FINAL SUSPECT RANKING ---")
    for r in data["rankings"]:
        print(f"Rank {r['rank']} (Initial {r['rank'] + r['rank_change']}): {r['vessel_name']} (Final Score: {r['final_score']})")
        print(f"  Explanation: {r['rank_change_explanation']}")
        print(f"  Priority: {r['investigation_priority']}")
        
        # Check forbidden words
        forbidden = ["guilty", "caused", "responsible", "proof"]
        explanation_lower = r['rank_change_explanation'].lower()
        for word in forbidden:
            assert word not in explanation_lower

    assert top_result["rank"] == 1
