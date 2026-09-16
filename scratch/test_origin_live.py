import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_origin_cone():
    res = client.get("/api/origin/test-id")
    assert res.status_code == 200
    data = res.json()
    assert "observed_slick_polygon" in data
    assert "time_window_start" in data
    assert "probable_origin" in data
    assert "trajectories" in data
    print("Origin Cone Data:", data)
