from __future__ import annotations

from typing import Protocol

import mss
import numpy as np

from autolook.types import Rect
from autolook.window.win32_window import configure_process_dpi_awareness


class FrameSource(Protocol):
    def grab(self) -> np.ndarray:
        """Return one BGR frame."""


class MssFrameSource:
    def __init__(self, region: Rect) -> None:
        configure_process_dpi_awareness()
        self.region = region
        self._sct = mss.mss()

    def grab(self) -> np.ndarray:
        monitor = {
            "left": self.region.left,
            "top": self.region.top,
            "width": self.region.width,
            "height": self.region.height,
        }
        frame = np.asarray(self._sct.grab(monitor))
        return frame[:, :, :3]
