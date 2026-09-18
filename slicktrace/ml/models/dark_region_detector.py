"""
SlickTrace v2 — Candidate Dark-Region Detector

Performs adaptive local thresholding (CFAR-inspired sliding window)
and connected-component morphological contour extraction on SAR calibrated dB imagery
to detect candidate dark formations on the sea surface.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from scipy.ndimage import uniform_filter, label, find_objects
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class DarkRegionCandidate:
    """Represents a segmented candidate dark formation with bounding box and mask."""

    def __init__(
        self,
        candidate_id: int,
        bbox: Tuple[int, int, int, int],  # (ymin, xmin, ymax, xmax)
        area_pixels: int,
        binary_mask: np.ndarray,
        centroid_px: Tuple[float, float],  # (row, col)
    ):
        self.candidate_id = candidate_id
        self.bbox = bbox
        self.area_pixels = area_pixels
        self.binary_mask = binary_mask
        self.centroid_px = centroid_px

    @property
    def mask(self) -> np.ndarray:
        return self.binary_mask


class DarkRegionDetector:
    """
    Identifies dark spot candidate regions on sea surfaces.
    """

    def __init__(
        self,
        window_size: int = 65,
        threshold_offset_db: float = 3.5,
        min_area_pixels: int = 40,
        max_area_fraction: float = 0.45,
    ):
        self.window_size = window_size
        self.threshold_offset_db = threshold_offset_db
        self.min_area_pixels = min_area_pixels
        self.max_area_fraction = max_area_fraction

    def detect_candidates(self, sar_db: np.ndarray) -> List[DarkRegionCandidate]:
        """
        Locates candidate dark formations where local backscatter drops significantly
        below surrounding sea clutter mean (CFAR-style adaptive contrast).

        Args:
            sar_db: 2D np.ndarray (H, W) float32 in decibels (or normalized)

        Returns:
            List of DarkRegionCandidate objects.
        """
        H, W = sar_db.shape
        max_pixels = int(H * W * self.max_area_fraction)

        # 1. Compute local background clutter mean
        if SCIPY_AVAILABLE:
            local_mean = uniform_filter(sar_db, size=self.window_size, mode="reflect")
        else:
            # Fallback simple mean
            local_mean = np.full_like(sar_db, np.mean(sar_db))

        # Damping condition: backscatter must be lower than local background clutter by threshold_offset
        dark_mask = sar_db < (local_mean - self.threshold_offset_db)

        # 2. Morphological cleanup (close gaps, remove single pixel salt)
        if CV2_AVAILABLE:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dark_clean = cv2.morphologyEx(dark_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
            dark_clean = cv2.morphologyEx(dark_clean, cv2.MORPH_CLOSE, kernel)
        else:
            dark_clean = dark_mask.astype(np.uint8)

        # 3. Connected component analysis
        candidates: List[DarkRegionCandidate] = []

        if CV2_AVAILABLE:
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dark_clean)
            for idx in range(1, num_labels):
                area = int(stats[idx, cv2.CC_STAT_AREA])
                if area < self.min_area_pixels or area > max_pixels:
                    continue

                xmin = int(stats[idx, cv2.CC_STAT_LEFT])
                ymin = int(stats[idx, cv2.CC_STAT_TOP])
                width = int(stats[idx, cv2.CC_STAT_WIDTH])
                height = int(stats[idx, cv2.CC_STAT_HEIGHT])
                ymax = ymin + height
                xmax = xmin + width

                cand_mask = labels[ymin:ymax, xmin:xmax] == idx
                centroid = (float(centroids[idx][1]), float(centroids[idx][0]))  # (row, col)

                candidates.append(
                    DarkRegionCandidate(
                        candidate_id=idx,
                        bbox=(ymin, xmin, ymax, xmax),
                        area_pixels=area,
                        binary_mask=cand_mask,
                        centroid_px=centroid,
                    )
                )
        elif SCIPY_AVAILABLE:
            labeled_arr, num_features = label(dark_clean)
            slices = find_objects(labeled_arr)
            for idx, sl in enumerate(slices, start=1):
                if sl is None:
                    continue
                cand_mask = labeled_arr[sl] == idx
                area = int(np.sum(cand_mask))
                if area < self.min_area_pixels or area > max_pixels:
                    continue

                ymin, ymax = sl[0].start, sl[0].stop
                xmin, xmax = sl[1].start, sl[1].stop
                r_indices, c_indices = np.where(cand_mask)
                centroid = (float(ymin + np.mean(r_indices)), float(xmin + np.mean(c_indices)))

                candidates.append(
                    DarkRegionCandidate(
                        candidate_id=idx,
                        bbox=(ymin, xmin, ymax, xmax),
                        area_pixels=area,
                        binary_mask=cand_mask,
                        centroid_px=centroid,
                    )
                )

        return candidates
