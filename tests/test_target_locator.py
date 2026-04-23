import numpy as np

from autolook.bot.selector import TargetSelector
from autolook.bot.target_locator import TargetLocator
from autolook.config import TargetPetConfig, TargetsConfig, VisionConfig
from autolook.types import Detection, Rect


class FakeDetector:
    def __init__(self) -> None:
        self.calls = 0

    def detect(self, frame: np.ndarray) -> list[Detection]:
        self.calls += 1
        return [Detection("target_pet", 0.95, Rect(10, 10, 8, 8))]


class MultiDetectionFakeDetector:
    def detect(self, frame: np.ndarray) -> list[Detection]:
        return [
            Detection("target_pet", 0.70, Rect(10, 10, 8, 8)),
            Detection("target_pet", 0.95, Rect(20, 20, 8, 8)),
            Detection("other", 0.99, Rect(30, 30, 8, 8)),
        ]


def _frame_with_marker(left: int, top: int) -> np.ndarray:
    frame = np.zeros((60, 60, 3), dtype=np.uint8)
    pattern = np.arange(64, dtype=np.uint8).reshape(8, 8) * 3
    frame[top : top + 8, left : left + 8] = np.dstack([pattern, pattern, pattern])
    return frame


def test_target_locator_uses_tracker_between_detector_runs() -> None:
    detector = FakeDetector()
    selector = TargetSelector(
        TargetsConfig(
            pets=[TargetPetConfig(name="target", detector_label="target_pet", min_confidence=0.6)]
        )
    )
    config = VisionConfig()
    config.tracking.detector_interval_frames = 10
    config.tracking.template_padding_px = 0
    locator = TargetLocator(detector, selector, config)

    first = locator.locate(_frame_with_marker(10, 10))
    second = locator.locate(_frame_with_marker(12, 13))

    assert detector.calls == 1
    assert first is not None
    assert second is not None
    assert second.box == Rect(12, 13, 8, 8)


def test_target_locator_returns_selected_target_and_all_candidates() -> None:
    selector = TargetSelector(
        TargetsConfig(
            pets=[TargetPetConfig(name="target", detector_label="target_pet", min_confidence=0.6)]
        )
    )
    config = VisionConfig()
    config.tracking.enabled = False
    locator = TargetLocator(MultiDetectionFakeDetector(), selector, config)

    location = locator.locate_frame(np.zeros((60, 60, 3), dtype=np.uint8))

    assert location.target is not None
    assert location.target.confidence == 0.95
    assert [detection.confidence for detection in location.candidates] == [0.70, 0.95]


def test_target_locator_can_force_detector_while_tracking() -> None:
    detector = FakeDetector()
    selector = TargetSelector(
        TargetsConfig(
            pets=[TargetPetConfig(name="target", detector_label="target_pet", min_confidence=0.6)]
        )
    )
    config = VisionConfig()
    config.tracking.detector_interval_frames = 10
    config.tracking.template_padding_px = 0
    locator = TargetLocator(detector, selector, config)

    locator.locate_frame(_frame_with_marker(10, 10))
    location = locator.locate_frame(_frame_with_marker(12, 13), force_detector=True)

    assert detector.calls == 2
    assert location.candidates == [Detection("target_pet", 0.95, Rect(10, 10, 8, 8))]
