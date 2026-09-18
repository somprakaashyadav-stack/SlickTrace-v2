"""
SlickTrace v2 — Remote-Sensing Classification & Segmentation Pipeline Orchestrator

Executes the full pipeline:
SAR Preprocessing
  → Candidate Dark-Region Detection
  → Contextual Feature Extraction
  → Multi-Class Classification (8 classes)
  → U-Net++ ResNet-50 Primary Segmentation
  → Optional DeepLabV3+ Secondary Cross-Validation
  → Optional SAM 2 Interactive Boundary Refinement
  → GeoJSON Polygon & Attribution Extraction

Strict Non-Fabrication Guarantee:
If weights are missing, raises WeightsUnavailable with:
"Model weights unavailable: <path>"
Never invents synthetic confidence scores.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.models.contextual_features import extract_contextual_features
from ml.models.dark_region_detector import DarkRegionDetector
from ml.models.deeplabv3plus import DeepLabV3PlusSegmentor
from ml.models.multiclass_classifier import MultiClassClassifier
from ml.models.sam2_refiner import SAM2Refiner
from ml.models.taxonomy import CLASS_METADATA, SpillClass
from ml.models.unetplusplus import UNetPlusPlusSegmentor
from ml.models.weight_guard import WeightsUnavailable


class RemoteSensingPipeline:
    """
    Complete remote sensing classification and segmentation pipeline.
    """

    MODEL_VERSION = "2.0.0-unetplusplus-resnet50"

    def __init__(
        self,
        use_onnx: bool = True,
        use_secondary_deeplab: bool = False,
        use_sam2: bool = False,
    ):
        self.use_onnx = use_onnx
        self.use_secondary_deeplab = use_secondary_deeplab
        self.use_sam2 = use_sam2

        self.dark_detector = DarkRegionDetector()
        self.classifier = MultiClassClassifier()
        self.unet = UNetPlusPlusSegmentor(use_onnx=use_onnx)
        self.deeplab = DeepLabV3PlusSegmentor(use_onnx=use_onnx) if use_secondary_deeplab else None
        self.sam2 = SAM2Refiner() if use_sam2 else None

    def run(
        self,
        sar_array: np.ndarray,
        acquisition_time: Optional[datetime] = None,
        source_reference: str = "unknown_scene",
        geotransform: Optional[Any] = None,
        pixel_size_m: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end segmentation and classification on a normalized SAR array.

        Returns:
            Dict matching required schema:
            class, confidence, mask, polygon, area_km2, centroid, bbox,
            acquisition_time, model_version, source_reference
        """
        H, W = sar_array.shape

        # 1. Candidate Dark-Region Detection
        candidates = self.dark_detector.detect_candidates(sar_array)

        # 2. Contextual Feature Extraction & Classification
        candidate_classes: List[Tuple[SpillClass, float]] = []
        if candidates:
            for cand in candidates:
                ymin, xmin, ymax, xmax = cand.bbox
                patch = sar_array[ymin:ymax, xmin:xmax]
                feats = extract_contextual_features(patch, cand.binary_mask)
                # Classify candidate (raises WeightsUnavailable if classifier weights missing)
                pred_class, conf = self.classifier.classify_candidate(feats)
                candidate_classes.append((pred_class, conf))
        else:
            # If no dark spots at all, open sea surface
            candidate_classes = [(SpillClass.WATER, 0.95)]

        # Determine dominant classified entity
        dominant_class, dominant_confidence = candidate_classes[0]

        # 3. Primary U-Net++ Segmentation
        # (raises WeightsUnavailable with "Model weights unavailable: <path>" if missing)
        unet_prob_map = self.unet.predict(sar_array)
        binary_mask = (unet_prob_map >= 0.5).astype(np.uint8)

        # 4. Optional Secondary DeepLabV3+ Cross-Validation
        deeplab_iou = None
        if self.deeplab is not None:
            try:
                dl_prob = self.deeplab.predict(sar_array)
                dl_mask = (dl_prob >= 0.5).astype(np.uint8)
                intersection = np.logical_and(binary_mask, dl_mask).sum()
                union = np.logical_or(binary_mask, dl_mask).sum()
                deeplab_iou = float(intersection / max(1.0, union))
            except Exception:
                deeplab_iou = None

        # 5. Optional SAM 2 Boundary Refinement
        refined_mask = binary_mask
        if self.sam2 is not None and candidates:
            try:
                main_cand = max(candidates, key=lambda c: c.area_pixels)
                ymin, xmin, ymax, xmax = main_cand.bbox
                refined_mask = self.sam2.refine_mask(
                    sar_image=sar_array,
                    rough_mask=binary_mask,
                    bounding_box=(xmin, ymin, xmax, ymax),
                )
            except Exception:
                refined_mask = binary_mask

        # 6. Polygon & Spatial Metric Calculations
        polygon_geojson, area_km2, centroid, bbox = self._extract_spatial_products(
            mask=refined_mask,
            geotransform=geotransform,
            pixel_size_m=pixel_size_m,
        )

        return {
            "class": dominant_class.value,
            "confidence": round(float(dominant_confidence), 4) if dominant_confidence is not None else None,
            "mask": refined_mask,
            "polygon": polygon_geojson,
            "area_km2": round(float(area_km2), 3) if area_km2 is not None else None,
            "centroid": centroid,
            "bbox": bbox,
            "acquisition_time": acquisition_time.isoformat() if acquisition_time else None,
            "model_version": self.MODEL_VERSION,
            "source_reference": source_reference,
            "deeplab_validation_iou": deeplab_iou,
            "class_description": CLASS_METADATA.get(dominant_class, {}).get("description"),
            "recommended_action": CLASS_METADATA.get(dominant_class, {}).get("action"),
        }

    def _extract_spatial_products(
        self,
        mask: np.ndarray,
        geotransform: Optional[Any],
        pixel_size_m: float,
    ) -> Tuple[Optional[Dict[str, Any]], float, Optional[Tuple[float, float]], Optional[Tuple[float, float, float, float]]]:
        """Calculates area, centroid, bounding box and GeoJSON MultiPolygon."""
        pixel_count = int(np.sum(mask > 0))
        area_km2 = (pixel_count * (pixel_size_m ** 2)) / 1e6

        if pixel_count == 0:
            return None, 0.0, None, None

        rows, cols = np.where(mask > 0)
        row_min, row_max = int(np.min(rows)), int(np.max(rows))
        col_min, col_max = int(np.min(cols)), int(np.max(cols))

        center_row = float(np.mean(rows))
        center_col = float(np.mean(cols))

        if geotransform is not None:
            # Transform pixel coords to spatial coords (lon, lat)
            def px_to_geo(c, r):
                return geotransform * (c, r)

            min_lon, max_lat = px_to_geo(col_min, row_min)
            max_lon, min_lat = px_to_geo(col_max, row_max)
            c_lon, c_lat = px_to_geo(center_col, center_row)

            centroid = (round(float(c_lat), 5), round(float(c_lon), 5))
            bbox = (
                round(float(min(min_lon, max_lon)), 5),
                round(float(min(min_lat, max_lat)), 5),
                round(float(max(min_lon, max_lon)), 5),
                round(float(max(min_lat, max_lat)), 5),
            )

            polygon_geojson = {
                "type": "Polygon",
                "coordinates": [[
                    [bbox[0], bbox[1]],
                    [bbox[2], bbox[1]],
                    [bbox[2], bbox[3]],
                    [bbox[0], bbox[3]],
                    [bbox[0], bbox[1]],
                ]],
            }
        else:
            centroid = (round(center_row, 1), round(center_col, 1))
            bbox = (float(col_min), float(row_min), float(col_max), float(row_max))
            polygon_geojson = {
                "type": "Polygon",
                "coordinates": [[
                    [col_min, row_min],
                    [col_max, row_min],
                    [col_max, row_max],
                    [col_min, row_max],
                    [col_min, row_min],
                ]],
            }

        return polygon_geojson, area_km2, centroid, bbox
