"""
SlickTrace v2 — Oil vs. Look-alike Classifier (XGBoost)

Classifies detected SAR dark patches as:
  1 = Oil spill (genuine)
  0 = Look-alike (wind rows, biogenic slick, ship wake, rain cells, low-wind areas)

Features derived from SAR texture statistics and shape descriptors extracted
from the segmentation mask and surrounding patch.

UNAVAILABLE guard: raises WeightsUnavailable if model weights not present.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

import numpy as np

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

from ml.models.weight_guard import WeightsUnavailable, require_weights

WEIGHTS_DIR = Path(os.environ.get("ML_WEIGHTS_DIR", "/app/weights"))
CLASSIFIER_WEIGHTS = WEIGHTS_DIR / "lookalike_xgb.ubj"

_FEATURE_NAMES = [
    "mean_backscatter",
    "std_backscatter",
    "min_backscatter",
    "max_backscatter",
    "area_px",
    "compactness",
    "elongation",
    "contrast",
    "homogeneity",
    "kurtosis",
    "skewness",
    "perimeter_px",
    "aspect_ratio",
]


def _kurtosis(x: np.ndarray) -> float:
    if x.std() == 0:
        return 0.0
    return float(np.mean(((x - x.mean()) / (x.std() + 1e-9)) ** 4) - 3)


def _skewness(x: np.ndarray) -> float:
    if x.std() == 0:
        return 0.0
    return float(np.mean(((x - x.mean()) / (x.std() + 1e-9)) ** 3))


def extract_sar_features(sar_patch: np.ndarray, mask: np.ndarray) -> Dict[str, float]:
    """
    Extract texture and shape features from a SAR patch within the spill mask.

    Args:
        sar_patch: np.ndarray (H, W) float32, normalised SAR backscatter
        mask: np.ndarray (H, W) float32, segmentation probability map

    Returns:
        dict of feature_name -> float value
    """
    binary = mask >= 0.5
    masked = sar_patch[binary]
    if masked.size == 0:
        return {k: 0.0 for k in _FEATURE_NAMES}

    area_px = float(binary.sum())
    rows_any = binary.any(axis=1)
    cols_any = binary.any(axis=0)
    height_bbox = float(rows_any.sum())
    width_bbox = float(cols_any.sum())
    bbox_area = height_bbox * width_bbox
    compactness = area_px / (bbox_area + 1e-9)
    aspect_ratio = width_bbox / (height_bbox + 1e-9)

    # Perimeter approximation (count boundary pixels)
    from scipy.ndimage import binary_erosion
    try:
        eroded = binary_erosion(binary)
        perimeter_px = float((binary ^ eroded).sum())
    except Exception:
        perimeter_px = 0.0

    return {
        "mean_backscatter": float(masked.mean()),
        "std_backscatter": float(masked.std()),
        "min_backscatter": float(masked.min()),
        "max_backscatter": float(masked.max()),
        "area_px": area_px,
        "compactness": compactness,
        "elongation": aspect_ratio,
        "contrast": float(masked.max() - masked.min()),
        "homogeneity": float(1.0 / (1.0 + masked.var())),
        "kurtosis": _kurtosis(masked),
        "skewness": _skewness(masked),
        "perimeter_px": perimeter_px,
        "aspect_ratio": aspect_ratio,
    }


class LookalikeClassifier:
    """
    XGBoost binary classifier: genuine oil spill (1) vs look-alike (0).

    Usage:
        clf = LookalikeClassifier()
        prob = clf.predict_proba(sar_patch, mask)  # float 0-1, P(oil)
    """

    def __init__(self, weights_path: Optional[Path] = None):
        self.weights_path = weights_path or CLASSIFIER_WEIGHTS
        self._model = None

    def load(self) -> None:
        if not XGB_AVAILABLE:
            raise ImportError("xgboost is not installed. pip install xgboost")
        require_weights(
            model_name="LookalikeClassifier XGBoost",
            weights_path=self.weights_path,
            instructions="Train or download from project releases. See ml/weights/README.md",
        )
        self._model = xgb.Booster()
        self._model.load_model(str(self.weights_path))

    def predict_proba(self, sar_patch: np.ndarray, mask: np.ndarray) -> float:
        """
        Returns P(oil) for the given SAR patch and spill mask.

        Raises:
            WeightsUnavailable: if model weights not present.
        """
        if self._model is None:
            self.load()

        features = extract_sar_features(sar_patch, mask)
        row = np.array([[features[k] for k in _FEATURE_NAMES]], dtype=np.float32)
        dmat = xgb.DMatrix(row, feature_names=_FEATURE_NAMES)
        prob = float(self._model.predict(dmat)[0])
        return min(max(prob, 0.0), 1.0)
