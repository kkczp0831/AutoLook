from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from autolook.config import VisionConfig
from autolook.types import Detection, Rect
from autolook.vision.detector import Detector


class YoloDetector(Detector):
    def __init__(self, config: VisionConfig) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "YOLO detection requires ultralytics. Install it with: "
                "python -m pip install -e .[yolo]"
            ) from exc

        self.model_path = Path(config.model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"YOLO model not found: {self.model_path}")

        self.confidence_threshold = float(config.yolo_confidence_threshold)
        self.image_size = (int(config.input_size.height), int(config.input_size.width))
        self._model = YOLO(str(self.model_path))
        self._names = getattr(self._model, "names", {})

    def detect(self, frame: np.ndarray) -> list[Detection]:
        results = self._model.predict(
            source=frame,
            imgsz=self.image_size,
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections: list[Detection] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            xyxy = self._to_numpy(getattr(boxes, "xyxy", []))
            confidences = self._to_numpy(getattr(boxes, "conf", []))
            classes = self._to_numpy(getattr(boxes, "cls", []))
            names = getattr(result, "names", None) or self._names

            for box, confidence, class_id in zip(xyxy, confidences, classes):
                left, top, right, bottom = [int(round(float(value))) for value in box[:4]]
                width = max(0, right - left)
                height = max(0, bottom - top)
                if width <= 0 or height <= 0:
                    continue

                detections.append(
                    Detection(
                        label=self._label_for_class(names, int(class_id)),
                        confidence=float(confidence),
                        box=Rect(left=left, top=top, width=width, height=height),
                    )
                )
        return detections

    @staticmethod
    def _to_numpy(value: Any) -> np.ndarray:
        if hasattr(value, "cpu"):
            value = value.cpu()
        if hasattr(value, "numpy"):
            return value.numpy()
        return np.asarray(value)

    @staticmethod
    def _label_for_class(names: Any, class_id: int) -> str:
        if isinstance(names, dict):
            return str(names.get(class_id, class_id))
        if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
            return str(names[class_id])
        return str(class_id)
