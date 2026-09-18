"""
SlickTrace v2 — DeepLabV3+ with ResNet-50 encoder for SAR oil-spill segmentation.

Secondary segmentation model used for cross-validation and ensemble agreement.
Supports ONNX Runtime and PyTorch backends.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np

from ml.models.weight_guard import WeightsUnavailable, require_weights

WEIGHTS_DIR = Path(os.environ.get("ML_WEIGHTS_DIR", "/app/weights"))
DEEPLAB_PTH = WEIGHTS_DIR / "deeplabv3plus_resnet50_sar.pth"
DEEPLAB_ONNX = WEIGHTS_DIR / "deeplabv3plus_resnet50_sar.onnx"
INPUT_SIZE = 512


class DeepLabV3PlusSegmentor:
    """
    DeepLabV3+ segmentor with ResNet-50 backbone.
    """

    def __init__(
        self,
        weights_path: Optional[Path] = None,
        device: Optional[str] = None,
        use_onnx: bool = True,
    ):
        self.weights_path = weights_path or DEEPLAB_PTH
        self.onnx_path = DEEPLAB_ONNX
        self.use_onnx = use_onnx
        self.device = device
        self._onnx_runner = None
        self._pytorch_model = None

    def load(self) -> None:
        if self.use_onnx and self.onnx_path.exists():
            from ml.models.onnx_runner import ONNXModelRunner
            self._onnx_runner = ONNXModelRunner(self.onnx_path)
            self._onnx_runner.load()
            return

        require_weights(
            model_name="DeepLabV3+ ResNet-50",
            weights_path=self.weights_path,
            instructions="Place deeplabv3plus_resnet50_sar.pth or .onnx at the configured path.",
        )

        import torch
        import torch.nn as nn
        try:
            import segmentation_models_pytorch as smp
        except ImportError:
            raise ImportError("segmentation_models_pytorch not installed.")

        dev = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        model = smp.DeepLabV3Plus(
            encoder_name="resnet50",
            encoder_weights=None,
            in_channels=1,
            classes=1,
            activation=None,
        )
        state = torch.load(self.weights_path, map_location=dev)
        model.load_state_dict(state)
        model.to(dev)
        model.eval()
        self._pytorch_model = (model, dev)

    def predict(self, sar_array: np.ndarray) -> np.ndarray:
        if self._onnx_runner is None and self._pytorch_model is None:
            self.load()

        if sar_array.ndim != 2:
            raise ValueError(f"Expected 2D array, got {sar_array.shape}")

        orig_shape = sar_array.shape

        if self._onnx_runner is not None:
            import cv2
            resized = cv2.resize(sar_array, (INPUT_SIZE, INPUT_SIZE), interpolation=cv2.INTER_LINEAR)
            tensor = resized[np.newaxis, np.newaxis, :, :]
            probs = self._onnx_runner.predict(tensor)[0, 0]
            out = cv2.resize(probs, (orig_shape[1], orig_shape[0]), interpolation=cv2.INTER_LINEAR)
            return out.astype(np.float32)

        import torch
        import torch.nn.functional as F

        model, dev = self._pytorch_model
        t = torch.from_numpy(sar_array).float().unsqueeze(0).unsqueeze(0)
        t = F.interpolate(t, size=(INPUT_SIZE, INPUT_SIZE), mode="bilinear", align_corners=False)
        t = t.to(dev)

        with torch.no_grad():
            logits = model(t)
            probs = torch.sigmoid(logits).squeeze().cpu()

        out = probs.unsqueeze(0).unsqueeze(0)
        out = F.interpolate(out, size=orig_shape, mode="bilinear", align_corners=False)
        return out.squeeze().numpy().astype(np.float32)
