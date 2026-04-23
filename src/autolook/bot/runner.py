from __future__ import annotations

import time

from autolook.bot.selector import TargetSelector
from autolook.bot.target_locator import TargetLocator
from autolook.bot.throw_controller import ThrowController
from autolook.capture import MssFrameSource
from autolook.config import Settings
from autolook.control import CameraAligner, create_input_controller
from autolook.types import BotState, Detection, TargetLocation
from autolook.vision import create_detector
from autolook.window import resolve_capture_region
from autolook.window.overlay import OverlayBox, Win32OverlayBorder


class BotRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.state = BotState.IDLE
        self.capture_region = resolve_capture_region(settings, debug=settings.app.debug)
        self.frame_source = MssFrameSource(self.capture_region)
        self.detector = create_detector(settings.vision)
        self.selector = TargetSelector(settings.targets)
        self.locator = TargetLocator(self.detector, self.selector, settings.vision)
        self.aligner = CameraAligner(settings.control.camera, self.capture_region)
        self.input = create_input_controller(settings.app.dry_run)
        self.thrower = ThrowController(self.input, settings.control.capture)
        self._camera_keys_holding: set[str] = set()
        self._last_debug_at = 0.0
        self._target_overlay: Win32OverlayBorder | None = None
        if self.settings.app.overlay_target:
            self._target_overlay = Win32OverlayBorder.from_hex_color(
                self.settings.app.overlay_color,
                self.settings.app.overlay_thickness,
                self.settings.app.overlay_candidate_color,
            )

    def run(self) -> None:
        started_at = time.monotonic()
        self.state = BotState.SEARCHING
        print(
            "AutoLook started. "
            f"dry_run={self.settings.app.dry_run}"
        )
        if self.settings.app.dry_run:
            print("[dry-run] live input is disabled; use --live to move the mouse/camera.")
        self._print_startup_debug()

        try:
            while self._should_continue(started_at):
                self._pump_overlay()
                frame = self.frame_source.grab()
                self._sync_aligner_viewport(frame)
                location = self.locator.locate_frame(
                    frame,
                    force_detector=self.settings.app.overlay_target,
                )
                target = location.target
                self._update_overlay(location)
                self._maybe_print_frame_debug(target)
                self._step_capture(target, now=time.monotonic())
                time.sleep(self.settings.app.tick_interval_seconds)
        finally:
            self._close_overlay()
            self._release_camera_keys(ignore_errors=True)
            self._cancel_throw_hold(ignore_errors=True)
            self.state = BotState.STOPPED
            print("AutoLook stopped.")

    def _should_continue(self, started_at: float) -> bool:
        max_runtime = self.settings.app.max_runtime_seconds
        if max_runtime <= 0:
            return True
        return time.monotonic() - started_at < max_runtime

    def _print_startup_debug(self) -> None:
        if not self.settings.app.debug:
            return

        template_count = len(getattr(self.detector, "templates", []))
        print(
            "[debug] "
            f"vision_backend={self.settings.vision.backend} "
            f"templates={template_count} "
            f"target_labels={self._target_labels_text()} "
            f"camera_tolerance={self.settings.control.camera.center_tolerance_px} "
            f"camera_keys=({self.settings.control.camera.key_left},"
            f"{self.settings.control.camera.key_right},"
            f"{self.settings.control.camera.key_up},"
            f"{self.settings.control.camera.key_down})"
        )

    def _maybe_print_frame_debug(self, target) -> None:
        if not self.settings.app.debug:
            return

        now = time.monotonic()
        if now - self._last_debug_at < self.settings.app.debug_interval_seconds:
            return
        self._last_debug_at = now

        if target is None:
            print("[debug] no target")
            return

        error_x, error_y = self.aligner.center_error(target)
        print(
            "[debug] target "
            f"label={target.label} score={target.confidence:.4f} "
            f"box=({target.box.left},{target.box.top},{target.box.width},{target.box.height}) "
            f"center_error=({error_x},{error_y}) "
            f"centered={self.aligner.is_centered(target)}"
        )

    def _target_labels_text(self) -> str:
        labels = [pet.detector_label for pet in self.settings.targets.pets if pet.enabled]
        return ",".join(labels) if labels else "-"

    def _step_capture(self, target, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now

        if self.thrower.is_holding:
            self.state = BotState.CAPTURING
            self._release_camera_keys()
            thrown = self.thrower.throw_ball(now)
            if thrown and self.settings.app.debug:
                print(
                    "[debug] action=release_throw "
                    f"button={self.settings.control.capture.ball_button}"
                )
            return

        if target is None:
            self.state = BotState.SEARCHING
            self._release_camera_keys()
            return

        if not self.aligner.is_centered(target):
            self.state = BotState.ALIGNING
            dx, dy = self.aligner.alignment_delta(target)
            self._move_camera_keys(dx, dy)
            return

        self.state = BotState.CAPTURING
        self._release_camera_keys()
        was_holding = self.thrower.is_holding
        thrown = self.thrower.throw_ball(now)
        if self.settings.app.debug:
            if thrown:
                print(
                    "[debug] action=release_throw "
                    f"button={self.settings.control.capture.ball_button}"
                )
            elif not was_holding and self.thrower.is_holding:
                print(
                    "[debug] action=hold_aim "
                    f"button={self.settings.control.capture.ball_button} "
                    f"hold_seconds={self.settings.control.capture.aim_hold_seconds}"
                )
            elif self.thrower.is_cooling_down(now):
                print(
                    "[debug] action=throw_cooldown "
                    f"cooldown_seconds={self.settings.control.capture.throw_cooldown_seconds}"
                )

    def _sync_aligner_viewport(self, frame) -> None:
        height, width = frame.shape[:2]
        self.aligner.set_viewport_size(int(width), int(height))

    def _move_camera_keys(self, dx: int, dy: int) -> None:
        keys = self._camera_keys_for_delta(dx, dy)
        if self.settings.app.debug:
            keys_text = ",".join(sorted(keys)) if keys else "-"
            print(f"[debug] action=move_camera_keys dx={dx} dy={dy} keys={keys_text}")
        self._sync_camera_keys(keys)

    def _camera_keys_for_delta(self, dx: int, dy: int) -> set[str]:
        config = self.settings.control.camera
        keys = set()
        if dx < 0:
            self._add_camera_key(keys, config.key_left)
        elif dx > 0:
            self._add_camera_key(keys, config.key_right)
        if dy < 0:
            self._add_camera_key(keys, config.key_up)
        elif dy > 0:
            self._add_camera_key(keys, config.key_down)
        return keys

    @staticmethod
    def _add_camera_key(keys: set[str], key: str) -> None:
        normalized = key.lower()
        if normalized and normalized != "none":
            keys.add(normalized)

    def _sync_camera_keys(self, keys: set[str]) -> None:
        for key in sorted(self._camera_keys_holding - keys):
            if self.settings.app.debug:
                print(f"[debug] action=key_up key={key}")
            self.input.key_up(key)
        for key in sorted(keys - self._camera_keys_holding):
            if self.settings.app.debug:
                print(f"[debug] action=key_down key={key}")
            self.input.key_down(key)
        self._camera_keys_holding = set(keys)

    def _release_camera_keys(self, *, ignore_errors: bool = False) -> None:
        if not ignore_errors:
            self._sync_camera_keys(set())
            return

        for key in sorted(self._camera_keys_holding):
            if self.settings.app.debug:
                print(f"[debug] action=key_up key={key}")
            try:
                self.input.key_up(key)
            except Exception as exc:
                if self.settings.app.debug:
                    print(f"[debug] cleanup=key_up_failed key={key} error={exc}")
            finally:
                self._camera_keys_holding.discard(key)

    def _cancel_throw_hold(self, *, ignore_errors: bool = False) -> None:
        if not ignore_errors:
            self.thrower.cancel_hold()
            return

        try:
            self.thrower.cancel_hold()
        except Exception as exc:
            if self.settings.app.debug:
                print(f"[debug] cleanup=mouse_up_failed error={exc}")

    def _pump_overlay(self) -> None:
        if self._target_overlay is not None:
            self._target_overlay.pump()

    def _update_overlay(self, location: TargetLocation | Detection | None) -> None:
        if self._target_overlay is None:
            return

        target, candidates = self._normalize_overlay_location(location)
        if not candidates:
            self._target_overlay.hide()
            return

        if not hasattr(self._target_overlay, "set_boxes"):
            if target is None:
                self._target_overlay.hide()
                return
            box = target.box
            self._target_overlay.set_rect(
                self.capture_region.left + box.left,
                self.capture_region.top + box.top,
                box.width,
                box.height,
            )
            return

        target_color = self._target_overlay.target_color_rgb
        candidate_color = self._target_overlay.candidate_color_rgb
        overlay_boxes = []
        for detection in candidates:
            color = target_color if target is not None and detection == target else candidate_color
            overlay_boxes.append(
                OverlayBox(
                    left=detection.box.left,
                    top=detection.box.top,
                    width=detection.box.width,
                    height=detection.box.height,
                    label=f"{detection.confidence:.2f}",
                    color_rgb=color,
                )
            )

        self._target_overlay.set_boxes(
            self.capture_region.left,
            self.capture_region.top,
            self.capture_region.width,
            self.capture_region.height,
            overlay_boxes,
        )

    @staticmethod
    def _normalize_overlay_location(
        location: TargetLocation | Detection | None,
    ) -> tuple[Detection | None, list[Detection]]:
        if location is None:
            return None, []
        if isinstance(location, TargetLocation):
            return location.target, location.candidates
        return location, [location]

    def _close_overlay(self) -> None:
        if self._target_overlay is not None:
            self._target_overlay.close()
            self._target_overlay = None
