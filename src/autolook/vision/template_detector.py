from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from autolook.types import Detection, Rect
from autolook.vision.detector import Detector


class TemplateMatchResult:
    def __init__(
        self,
        label: str,
        confidence: float,
        box: Rect,
        template_name: str,
    ) -> None:
        self.label = label
        self.confidence = confidence
        self.box = box
        self.template_name = template_name


class TemplateDetector(Detector):
    def __init__(self, template_dir: Path, threshold: float = 0.75) -> None:
        self.threshold = threshold
        self.templates = self._load_templates(template_dir)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        return [
            Detection(label=result.label, confidence=result.confidence, box=result.box)
            for result in self.match(frame)
            if result.confidence >= self.threshold
        ]

    def match(self, frame: np.ndarray) -> list[TemplateMatchResult]:
        matches: list[TemplateMatchResult] = []
        if not self.templates:
            return matches

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for label, template_name, template in self.templates:
            if template.shape[0] > gray.shape[0] or template.shape[1] > gray.shape[1]:
                continue
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            height, width = template.shape[:2]
            matches.append(
                TemplateMatchResult(
                    label=label,
                    confidence=float(max_val),
                    box=Rect(left=max_loc[0], top=max_loc[1], width=width, height=height),
                    template_name=template_name,
                )
            )
        return matches

    def _load_templates(self, template_dir: Path) -> list[tuple[str, str, np.ndarray]]:
        templates: list[tuple[str, str, np.ndarray]] = []
        if not template_dir.exists():
            return templates

        # New structure: data/templates/<detector_label>/*.png
        for label_dir in template_dir.iterdir():
            if not label_dir.is_dir():
                continue
            for path in sorted(label_dir.glob("*.png")):
                image = self._read_grayscale(path)
                if image is not None:
                    templates.append((label_dir.name, path.name, image))

        # Backward-compatible structure: data/templates/<detector_label>.png
        for path in template_dir.glob("*.png"):
            image = self._read_grayscale(path)
            if image is not None:
                templates.append((path.stem, path.name, image))
        return templates

    @staticmethod
    def _read_grayscale(path: Path) -> np.ndarray | None:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
