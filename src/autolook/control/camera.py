from __future__ import annotations

from autolook.config import CameraConfig
from autolook.types import Detection, Rect


class CameraAligner:
    def __init__(self, config: CameraConfig, viewport: Rect) -> None:
        self.config = config
        self.viewport = viewport

    def set_viewport_size(self, width: int, height: int) -> None:
        self.viewport = Rect(left=0, top=0, width=width, height=height)

    def alignment_delta(self, detection: Detection) -> tuple[int, int]:
        error_x, error_y = self.center_error(detection)

        dx = 0 if abs(error_x) <= self.config.center_tolerance_px else _sign(error_x)
        dy = 0 if abs(error_y) <= self.config.center_tolerance_px else _sign(error_y)
        return dx, dy

    def center_error(self, detection: Detection) -> tuple[int, int]:
        target_x, target_y = detection.center
        center_x, center_y = self.viewport.width // 2, self.viewport.height // 2
        error_x = target_x - center_x
        error_y = target_y - center_y
        return error_x, error_y

    def is_centered(self, detection: Detection) -> bool:
        error_x, error_y = self.center_error(detection)
        return (
            abs(error_x) <= self.config.center_tolerance_px
            and abs(error_y) <= self.config.center_tolerance_px
        )


def _sign(value: int) -> int:
    return -1 if value < 0 else 1
