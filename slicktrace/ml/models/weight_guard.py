"""
SlickTrace v2 — ML Weight Guard

All ML models must call `require_weights()` before inference.
If weights are missing, raises WeightsUnavailable with:
"Model weights unavailable: <configured_path>"
Never fabricates synthetic confidence or mock predictions.
"""
from __future__ import annotations

from pathlib import Path


class WeightsUnavailable(Exception):
    """
    Raised when model weights are not present on disk.
    Consumers must catch this and return an UNAVAILABLE state — never swallow it.
    """
    def __init__(self, model_name: str, weights_path: Path, instructions: str = ""):
        self.model_name = model_name
        self.weights_path = weights_path
        self.instructions = instructions
        msg = (
            f"[UNAVAILABLE] Model weights unavailable. "
            f"Configured model path: '{weights_path}'. "
            f"Model: '{model_name}'. {instructions}"
        )
        super().__init__(msg)


def require_weights(model_name: str, weights_path: Path, instructions: str = "") -> None:
    """
    Assert that weights exist at `weights_path`.
    Raises WeightsUnavailable if not.
    """
    if not weights_path.exists():
        raise WeightsUnavailable(model_name, weights_path, instructions)
