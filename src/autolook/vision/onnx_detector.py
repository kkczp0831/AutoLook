from __future__ import annotations

from pathlib import Path

import numpy as np

from autolook.types import Detection
from autolook.vision.detector import Detector


class OnnxDetector(Detector):
    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self._session = None

    def detect(self, frame: np.ndarray) -> list[Detection]:
        raise NotImplementedError(
            "ONNX detection is a placeholder. Add preprocessing, inference, and NMS here."
        )
