from __future__ import annotations

from autolook.config import TargetsConfig
from autolook.types import Detection


class TargetSelector:
    def __init__(self, targets: TargetsConfig) -> None:
        self.targets = targets

    def candidates(self, detections: list[Detection]) -> list[Detection]:
        enabled_targets = {
            pet.detector_label: pet.min_confidence for pet in self.targets.pets if pet.enabled
        }
        return [
            detection
            for detection in detections
            if detection.label in enabled_targets
            and detection.confidence >= enabled_targets[detection.label]
        ]

    def choose(self, detections: list[Detection]) -> Detection | None:
        candidates = self.candidates(detections)
        return self.choose_from_candidates(candidates)

    def choose_from_candidates(self, candidates: list[Detection]) -> Detection | None:
        if not candidates:
            return None
        return max(candidates, key=lambda detection: detection.confidence)
