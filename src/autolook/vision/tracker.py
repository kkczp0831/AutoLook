from __future__ import annotations

from typing import Protocol

import cv2
import numpy as np

from autolook.config import TrackingConfig
from autolook.types import Detection, Rect


class Tracker(Protocol):
    @property
    def has_target(self) -> bool:
        """Return whether the tracker has an active target."""

    def reset(self, detection: Detection, frame: np.ndarray) -> None:
        """Seed the tracker from a detector result."""

    def update(self, frame: np.ndarray) -> Detection | None:
        """Track the active target in the new frame."""


class LocalTemplateTracker:
    def __init__(self, config: TrackingConfig) -> None:
        self.config = config
        self._label: str | None = None
        self._template: np.ndarray | None = None
        self._last_box: Rect | None = None
        self._target_offset: tuple[int, int] = (0, 0)
        self._target_size: tuple[int, int] = (0, 0)
        self._misses = 0

    @property
    def has_target(self) -> bool:
        return self._template is not None and self._last_box is not None

    def reset(self, detection: Detection, frame: np.ndarray) -> None:
        height, width = frame.shape[:2]
        padded = self._clamp_rect(self._pad_rect(detection.box), width, height)
        if padded.width <= 0 or padded.height <= 0:
            self.clear()
            return

        crop = frame[padded.top : padded.top + padded.height, padded.left : padded.left + padded.width]
        if crop.size == 0:
            self.clear()
            return

        self._label = detection.label
        self._template = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        self._last_box = detection.box
        self._target_offset = (detection.box.left - padded.left, detection.box.top - padded.top)
        self._target_size = (detection.box.width, detection.box.height)
        self._misses = 0

    def update(self, frame: np.ndarray) -> Detection | None:
        if not self.has_target or self._template is None or self._last_box is None:
            return None

        height, width = frame.shape[:2]
        search_area = self._clamp_rect(
            self._expand_rect(self._last_box, self.config.search_margin_px),
            width,
            height,
        )
        if (
            search_area.width < self._template.shape[1]
            or search_area.height < self._template.shape[0]
        ):
            return self._mark_miss()

        crop = frame[
            search_area.top : search_area.top + search_area.height,
            search_area.left : search_area.left + search_area.width,
        ]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(gray, self._template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < self.config.min_confidence:
            return self._mark_miss()

        offset_x, offset_y = self._target_offset
        target_width, target_height = self._target_size
        box = Rect(
            left=search_area.left + max_loc[0] + offset_x,
            top=search_area.top + max_loc[1] + offset_y,
            width=target_width,
            height=target_height,
        )
        self._last_box = box
        self._misses = 0
        return Detection(label=self._label or "tracked_target", confidence=float(max_val), box=box)

    def clear(self) -> None:
        self._label = None
        self._template = None
        self._last_box = None
        self._target_offset = (0, 0)
        self._target_size = (0, 0)
        self._misses = 0

    def _mark_miss(self) -> Detection | None:
        self._misses += 1
        if self._misses > self.config.max_stale_frames:
            self.clear()
        return None

    def _pad_rect(self, rect: Rect) -> Rect:
        padding = self.config.template_padding_px
        return Rect(
            left=rect.left - padding,
            top=rect.top - padding,
            width=rect.width + padding * 2,
            height=rect.height + padding * 2,
        )

    @staticmethod
    def _expand_rect(rect: Rect, margin: int) -> Rect:
        return Rect(
            left=rect.left - margin,
            top=rect.top - margin,
            width=rect.width + margin * 2,
            height=rect.height + margin * 2,
        )

    @staticmethod
    def _clamp_rect(rect: Rect, max_width: int, max_height: int) -> Rect:
        left = max(0, rect.left)
        top = max(0, rect.top)
        right = min(max_width, rect.left + rect.width)
        bottom = min(max_height, rect.top + rect.height)
        return Rect(left=left, top=top, width=max(0, right - left), height=max(0, bottom - top))
