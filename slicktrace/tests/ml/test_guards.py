"""
SlickTrace v2 — ML Weight Guard & Architecture Tests
"""
import pytest
from pathlib import Path
from ml.models.weight_guard import WeightsUnavailable, require_weights
from ml.models.lookalike_classifier import extract_sar_features
import numpy as np


def test_require_weights_raises_unavailable(tmp_path):
    fake_path = tmp_path / "non_existent_weights.pth"
    with pytest.raises(WeightsUnavailable) as excinfo:
        require_weights("TestModel", fake_path, "Run scripts/download_weights.sh")
    assert "UNAVAILABLE" in str(excinfo.value)
    assert "TestModel" in str(excinfo.value)


def test_extract_sar_features():
    patch = np.random.uniform(0.0, 1.0, (100, 100)).astype(np.float32)
    mask = np.zeros((100, 100), dtype=np.float32)
    mask[40:60, 40:60] = 1.0

    features = extract_sar_features(patch, mask)
    assert "mean_backscatter" in features
    assert "compactness" in features
    assert "skewness" in features
    assert features["area_px"] == 400.0
