from __future__ import annotations

import numpy as np

from autolook.bot.selector import TargetSelector
from autolook.config import VisionConfig
from autolook.types import Detection, TargetLocation
from autolook.vision.detector import Detector
from autolook.vision.tracker import LocalTemplateTracker


class TargetLocator:
    def __init__(
        self,
        detector: Detector,
        selector: TargetSelector,
        vision_config: VisionConfig,
    ) -> None:
        self.detector = detector
        self.selector = selector
        self.config = vision_config
        self.tracker = LocalTemplateTracker(vision_config.tracking)
        self.frame_index = 0

    def locate(self, frame: np.ndarray) -> Detection | None:
        return self.locate_frame(frame).target

    def locate_frame(self, frame: np.ndarray, *, force_detector: bool = False) -> TargetLocation:
        self.frame_index += 1

        tracked = None
        if self.config.tracking.enabled and self.tracker.has_target:
            tracked = self.tracker.update(frame)

        if self._should_run_detector(tracked, force_detector=force_detector):
            candidates = self.selector.candidates(self.detector.detect(frame))
            detected = self.selector.choose_from_candidates(candidates)
            if detected is not None:
                if self.config.tracking.enabled:
                    self.tracker.reset(detected, frame)
                return TargetLocation(target=detected, candidates=candidates)

        candidates = [tracked] if tracked is not None else []
        return TargetLocation(target=tracked, candidates=candidates)

    def _should_run_detector(
        self,
        tracked: Detection | None,
        *,
        force_detector: bool = False,
    ) -> bool:
        if force_detector:
            return True

        if tracked is None:
            return True

        interval = self.config.tracking.detector_interval_frames
        if interval <= 0:
            return False

        return self.frame_index % interval == 0
