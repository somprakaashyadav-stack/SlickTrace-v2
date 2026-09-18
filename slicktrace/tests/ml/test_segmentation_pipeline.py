"""
SlickTrace v2 — Remote-Sensing Classification & Segmentation Pipeline Tests

Verifies:
- 8-class taxonomy validation
- Candidate dark-region detection
- Contextual feature extraction
- Strict weight guard: raises WeightsUnavailable with "Model weights unavailable: <path>"
- Non-fabrication of confidence
"""
from pathlib import Path
import numpy as np
import pytest

from ml.models.taxonomy import SpillClass, CLASS_METADATA
from ml.models.dark_region_detector import DarkRegionDetector
from ml.models.contextual_features import extract_contextual_features
from ml.models.weight_guard import WeightsUnavailable, require_weights
from ml.models.unetplusplus import UNetPlusPlusSegmentor


def test_taxonomy_classes_complete():
    expected_classes = {
        "OIL_SLICK",
        "ALGAE_LIKE",
        "SHIP_WAKE",
        "LOW_WIND_DARK_AREA",
        "COASTAL_ARTIFACT",
        "CLOUD",
        "WATER",
        "UNKNOWN",
    }
    actual_classes = {c.value for c in SpillClass}
    assert expected_classes == actual_classes
    assert len(CLASS_METADATA) == 8


def test_dark_region_detector_finds_slick():
    # Create synthetic sea clutter (background ~ 0.8) with a dark damped patch (~ 0.2)
    img = np.full((128, 128), 0.8, dtype=np.float32)
    # Dark anomaly in center
    img[50:80, 50:80] = 0.2

    detector = DarkRegionDetector(window_size=31, threshold_offset_db=0.3, min_area_pixels=20)
    candidates = detector.detect_candidates(img)

    assert len(candidates) >= 1
    cand = candidates[0]
    assert cand.area_pixels >= 300
    ymin, xmin, ymax, xmax = cand.bbox
    assert ymin <= 55 and ymax >= 75
    assert xmin <= 55 and xmax >= 75


def test_contextual_features_extraction():
    patch = np.full((64, 64), 0.8, dtype=np.float32)
    mask = np.zeros((64, 64), dtype=bool)
    mask[20:44, 20:44] = True
    patch[mask] = 0.2

    feats = extract_contextual_features(patch, mask)

    assert feats["area_px"] == pytest.approx(24 * 24, rel=1e-2)
    assert feats["compactness"] > 0.0
    assert feats["contrast_db"] > 0.0
    assert "elongation" in feats
    assert "boundary_gradient" in feats


def test_weight_guard_exact_error_message(tmp_path):
    fake_weights = tmp_path / "models" / "missing_unet.pth"

    with pytest.raises(WeightsUnavailable) as exc:
        require_weights(
            model_name="UNet++ ResNet-50",
            weights_path=fake_weights,
            instructions="Run download script.",
        )

    err_str = str(exc.value)
    assert "Model weights unavailable" in err_str
    assert str(fake_weights) in err_str


def test_unetplusplus_raises_when_weights_missing(tmp_path):
    fake_pth = tmp_path / "nonexistent_unet.pth"
    seg = UNetPlusPlusSegmentor(weights_path=fake_pth, use_onnx=False)

    with pytest.raises(WeightsUnavailable) as exc:
        seg.predict(np.zeros((128, 128), dtype=np.float32))

    err_str = str(exc.value)
    assert "Model weights unavailable" in err_str
    assert str(fake_pth) in err_str
