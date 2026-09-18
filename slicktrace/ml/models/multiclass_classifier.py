"""
SlickTrace v2 — Multi-Class Remote-Sensing Classifier

Categorizes candidate dark formations into the 8 standardized classes:
OIL_SLICK, ALGAE_LIKE, SHIP_WAKE, LOW_WIND_DARK_AREA,
COASTAL_ARTIFACT, CLOUD, WATER, UNKNOWN.

Uses contextual morphological & radiometric features.
Enforces weight guard: if trained classifier model weights are missing,
raises WeightsUnavailable and never fabricates confidence.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from ml.models.taxonomy import SpillClass
from ml.models.weight_guard import WeightsUnavailable, require_weights

WEIGHTS_DIR = Path(os.environ.get("ML_WEIGHTS_DIR", "/app/weights"))
CLASSIFIER_MODEL_PATH = WEIGHTS_DIR / "multiclass_lookalike_classifier.ubj"


class MultiClassClassifier:
    """
    Contextual classifier mapping candidate features to one of the 8 SpillClass types.
    """

    def __init__(self, weights_path: Optional[Path] = None):
        self.weights_path = weights_path or CLASSIFIER_MODEL_PATH
        self._booster = None

    def load(self) -> None:
        """Loads trained multi-class XGBoost model. Raises WeightsUnavailable if missing."""
        require_weights(
            model_name="MultiClassClassifier",
            weights_path=self.weights_path,
            instructions="Place trained XGBoost multi-class weights at the configured path.",
        )

        try:
            import xgboost as xgb
            self._booster = xgb.Booster()
            self._booster.load_model(str(self.weights_path))
        except ImportError:
            raise RuntimeError("xgboost not installed. pip install xgboost")

    def classify_candidate(
        self,
        features: Dict[str, float],
    ) -> Tuple[SpillClass, float]:
        """
        Classifies candidate dark feature dictionary.

        Returns: (predicted_class: SpillClass, confidence: float 0.0-1.0)
        Raises: WeightsUnavailable if weights missing.
        """
        if self._booster is None:
            self.load()

        import xgboost as xgb
        feature_keys = [
            "area_px", "compactness", "elongation", "complexity", "perimeter_px",
            "slick_mean_db", "slick_std", "bg_mean_db", "bg_std", "contrast_db",
            "boundary_gradient",
        ]
        row = np.array([[features.get(k, 0.0) for k in feature_keys]], dtype=np.float32)
        dmat = xgb.DMatrix(row, feature_names=feature_keys)
        probs = self._booster.predict(dmat)[0]

        classes = [
            SpillClass.OIL_SLICK,
            SpillClass.ALGAE_LIKE,
            SpillClass.SHIP_WAKE,
            SpillClass.LOW_WIND_DARK_AREA,
            SpillClass.COASTAL_ARTIFACT,
            SpillClass.CLOUD,
            SpillClass.WATER,
            SpillClass.UNKNOWN,
        ]

        best_idx = int(np.argmax(probs))
        confidence = float(probs[best_idx])
        return classes[best_idx], confidence
