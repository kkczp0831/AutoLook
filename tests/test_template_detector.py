import shutil
from pathlib import Path

import cv2
import numpy as np

from autolook.vision.template_detector import TemplateDetector


def test_template_detector_uses_directory_name_as_label() -> None:
    template_root = Path("tests/fixtures/generated/template_detector")
    if template_root.exists():
        shutil.rmtree(template_root)
    label_dir = template_root / "恶魔狼"
    label_dir.mkdir(parents=True)
    template = np.array(
        [
            [0, 255, 0, 255],
            [255, 0, 255, 0],
            [0, 255, 255, 0],
            [255, 0, 0, 255],
        ],
        dtype=np.uint8,
    )
    success, encoded = cv2.imencode(".png", template)
    assert success
    encoded.tofile(label_dir / "front.png")

    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    frame[8:12, 7:11] = np.dstack([template, template, template])
    detector = TemplateDetector(template_root, threshold=0.9)

    detections = detector.detect(frame)

    assert len(detections) == 1
    assert detections[0].label == "恶魔狼"

    shutil.rmtree(template_root)
