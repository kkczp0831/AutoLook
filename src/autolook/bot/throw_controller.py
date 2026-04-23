from __future__ import annotations

import time

from autolook.config import CaptureControlConfig
from autolook.control.input_controller import InputController


class ThrowController:
    def __init__(
        self,
        input_controller: InputController,
        capture_config: CaptureControlConfig,
    ) -> None:
        self.input = input_controller
        self.capture_config = capture_config
        self._hold_started_at: float | None = None
        self._last_throw_at: float | None = None

    @property
    def is_holding(self) -> bool:
        return self._hold_started_at is not None

    def throw_ball(self, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now

        if self._hold_started_at is not None:
            if now - self._hold_started_at < self.capture_config.aim_hold_seconds:
                return False
            self.input.mouse_up(self.capture_config.ball_button)
            self._hold_started_at = None
            self._last_throw_at = now
            return True

        if self.is_cooling_down(now):
            return False

        self.input.mouse_down(self.capture_config.ball_button)
        self._hold_started_at = now

        if self.capture_config.aim_hold_seconds <= 0:
            self.input.mouse_up(self.capture_config.ball_button)
            self._hold_started_at = None
            self._last_throw_at = now
            return True

        return False

    def is_cooling_down(self, now: float | None = None) -> bool:
        if self._last_throw_at is None:
            return False
        now = time.monotonic() if now is None else now
        return now - self._last_throw_at < self.capture_config.throw_cooldown_seconds

    def cancel_hold(self) -> None:
        self.input.mouse_up(self.capture_config.ball_button)
        self._hold_started_at = None
