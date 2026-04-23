from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from autolook.config import VisionConfig, VisionInputSize
from autolook.types import Rect
from autolook.vision.yolo_detector import YoloDetector


class FakeTensor:
    def __init__(self, value) -> None:
        self.value = np.asarray(value)

    def cpu(self):
        return self

    def numpy(self) -> np.ndarray:
        return self.value


class FakeYOLO:
    instances: list["FakeYOLO"] = []

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.names = {0: "恶魔狼", 1: "other"}
        self.predict_kwargs = {}
        FakeYOLO.instances.append(self)

    def predict(self, **kwargs):
        self.predict_kwargs = kwargs
        boxes = SimpleNamespace(
            xyxy=FakeTensor([[10.2, 20.6, 50.8, 80.1], [3, 4, 3, 10]]),
            conf=FakeTensor([0.91, 0.5]),
            cls=FakeTensor([0, 1]),
        )
        return [SimpleNamespace(boxes=boxes, names=self.names)]


def test_yolo_detector_converts_ultralytics_results_to_detections(monkeypatch) -> None:
    FakeYOLO.instances.clear()
    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(YOLO=FakeYOLO))
    model_path = Path("tests/fixtures/generated/yolo_detector/best.pt")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"fake")
    config = VisionConfig(
        backend="yolo",
        model_path=model_path,
        yolo_confidence_threshold=0.15,
        input_size=VisionInputSize(width=640, height=480),
    )

    try:
        detector = YoloDetector(config)
        detections = detector.detect(np.zeros((100, 100, 3), dtype=np.uint8))

        assert len(detections) == 1
        assert detections[0].label == "恶魔狼"
        assert detections[0].confidence == 0.91
        assert detections[0].box == Rect(left=10, top=21, width=41, height=59)

        instance = FakeYOLO.instances[0]
        assert instance.model_path == str(model_path)
        assert instance.predict_kwargs["imgsz"] == (480, 640)
        assert instance.predict_kwargs["conf"] == 0.15
        assert instance.predict_kwargs["verbose"] is False
    finally:
        model_path.unlink(missing_ok=True)
