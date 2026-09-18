"""
SlickTrace v2 — SAM 2 Mask Refinement Adapter.

Optional post-processing: uses Segment Anything Model 2 to refine coarse
segmentation masks into higher-fidelity spill polygon boundaries.

UNAVAILABLE: raises SAM2RefinerUnavailable if sam2 package or weights missing.
The pipeline continues without refinement if unavailable — callers must catch.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np

from ml.models.weight_guard import WeightsUnavailable, require_weights

WEIGHTS_DIR = Path(os.environ.get("ML_WEIGHTS_DIR", "/app/weights"))
SAM2_WEIGHTS = WEIGHTS_DIR / "sam2_hiera_large.pt"

try:
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    SAM2_AVAILABLE = True
except ImportError:
    SAM2_AVAILABLE = False


class SAM2RefinerUnavailable(Exception):
    """Raised when SAM2 is not available (package missing or weights not downloaded)."""
    pass


class SAM2Refiner:
    """
    Refines a binary segmentation mask using SAM 2 prompted with the
    bounding box of the detected spill region.

    If SAM2 is unavailable, raises SAM2RefinerUnavailable.
    Callers should catch and proceed without refinement — never block pipeline.
    """

    def __init__(self, weights_path: Optional[Path] = None, device: Optional[str] = None):
        self.weights_path = weights_path or SAM2_WEIGHTS
        self.device = device or "cpu"
        self._predictor = None

    def load(self) -> None:
        if not SAM2_AVAILABLE:
            raise SAM2RefinerUnavailable(
                "SAM2 package not installed. "
                "pip install git+https://github.com/facebookresearch/segment-anything-2.git"
            )
        require_weights(
            model_name="SAM2 Hiera Large",
            weights_path=self.weights_path,
            instructions="Download from https://dl.fbaipublicfiles.com/segment_anything_2/",
        )
        model = build_sam2("sam2_hiera_l.yaml", str(self.weights_path), device=self.device)
        self._predictor = SAM2ImagePredictor(model)

    def refine(self, image_rgb: np.ndarray, coarse_mask: np.ndarray) -> np.ndarray:
        """
        Refine a coarse binary mask using SAM2 bounding box prompt.

        Args:
            image_rgb: np.ndarray (H, W, 3) uint8
            coarse_mask: np.ndarray (H, W) bool — coarse spill mask

        Returns:
            refined_mask: np.ndarray (H, W) bool

        Raises:
            SAM2RefinerUnavailable: if SAM2 not loaded
        """
        if self._predictor is None:
            self.load()

        if not coarse_mask.any():
            return coarse_mask

        rows = np.any(coarse_mask, axis=1)
        cols = np.any(coarse_mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        bbox = np.array([cmin, rmin, cmax, rmax])  # x1, y1, x2, y2

        self._predictor.set_image(image_rgb)
        masks, scores, _ = self._predictor.predict(
            box=bbox[None, :],
            multimask_output=False,
        )
        return masks[0].astype(bool)
