"""
SlickTrace v2 — ONNX Runtime Inference Runner

Accelerates U-Net++ and DeepLabV3+ segmentation execution using ONNX Runtime
with CPU and CUDA execution providers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import numpy as np

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from ml.models.weight_guard import WeightsUnavailable, require_weights


class ONNXModelRunner:
    """
    Runs inference on exported ONNX segmentation models.
    """

    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._session = None

    def load(self) -> None:
        """Loads ONNX session. Raises WeightsUnavailable if .onnx file missing."""
        require_weights("ONNXModelRunner", self.model_path)

        if not ONNX_AVAILABLE:
            raise RuntimeError("onnxruntime is not installed. pip install onnxruntime")

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        available_providers = ort.get_available_providers()
        selected_providers = [p for p in providers if p in available_providers]

        self._session = ort.InferenceSession(str(self.model_path), providers=selected_providers)

    def predict(self, input_tensor: np.ndarray) -> np.ndarray:
        """
        Runs inference on 4D float32 numpy array (B, C, H, W).
        Returns output probability map (B, Classes, H, W).
        """
        if self._session is None:
            self.load()

        input_name = self._session.get_inputs()[0].name
        output_name = self._session.get_outputs()[0].name

        raw_out = self._session.run([output_name], {input_name: input_tensor.astype(np.float32)})[0]
        # Apply sigmoid
        probs = 1.0 / (1.0 + np.exp(-raw_out))
        return probs
