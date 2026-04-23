import numpy as np

from autolook.config import TrackingConfig
from autolook.types import Detection, Rect
from autolook.vision.tracker import LocalTemplateTracker


def _frame_with_pattern(left: int, top: int) -> np.ndarray:
    frame = np.zeros((60, 60, 3), dtype=np.uint8)
    pattern = np.array(
        [
            [0, 255, 0, 255, 0, 255, 0, 255],
            [255, 0, 255, 0, 255, 0, 255, 0],
            [0, 255, 255, 255, 255, 255, 255, 0],
            [255, 0, 255, 0, 0, 255, 0, 255],
            [0, 255, 255, 0, 0, 255, 255, 0],
            [255, 0, 255, 255, 255, 255, 0, 255],
            [0, 255, 0, 255, 0, 255, 0, 255],
            [255, 0, 255, 0, 255, 0, 255, 0],
        ],
        dtype=np.uint8,
    )
    frame[top : top + 8, left : left + 8] = np.dstack([pattern, pattern, pattern])
    return frame


def test_local_template_tracker_follows_nearby_motion() -> None:
    tracker = LocalTemplateTracker(
        TrackingConfig(search_margin_px=12, min_confidence=0.8, template_padding_px=0)
    )
    tracker.reset(Detection("target_pet", 0.95, Rect(10, 10, 8, 8)), _frame_with_pattern(10, 10))

    tracked = tracker.update(_frame_with_pattern(14, 16))

    assert tracked is not None
    assert tracked.label == "target_pet"
    assert tracked.box == Rect(14, 16, 8, 8)
