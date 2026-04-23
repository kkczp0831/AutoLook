from autolook.bot.runner import BotRunner
from autolook.bot.throw_controller import ThrowController
from autolook.config import (
    AppConfig,
    CameraConfig,
    CaptureControlConfig,
    ControlConfig,
    Settings,
)
from autolook.control.camera import CameraAligner
from autolook.types import BotState, Detection, Rect


class FakeInput:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def move_mouse(self, dx: int, dy: int) -> None:
        self.events.append(("move_mouse", f"{dx},{dy}"))

    def key_down(self, key: str) -> None:
        self.events.append(("key_down", key))

    def key_up(self, key: str) -> None:
        self.events.append(("key_up", key))

    def mouse_down(self, button: str) -> None:
        self.events.append(("mouse_down", button))

    def mouse_up(self, button: str) -> None:
        self.events.append(("mouse_up", button))

    def press_key(self, key: str) -> None:
        self.events.append(("press_key", key))


class FailingReleaseInput(FakeInput):
    def key_up(self, key: str) -> None:
        super().key_up(key)
        raise RuntimeError(f"cannot release {key}")

    def mouse_up(self, button: str) -> None:
        super().mouse_up(button)
        raise RuntimeError(f"cannot release {button}")


def make_runner(capture: CaptureControlConfig | None = None) -> BotRunner:
    camera = CameraConfig(center_tolerance_px=10)
    capture_config = capture or CaptureControlConfig()
    settings = Settings(
        app=AppConfig(debug=False),
        control=ControlConfig(camera=camera, capture=capture_config),
    )
    fake_input = FakeInput()
    runner = BotRunner.__new__(BotRunner)
    runner.settings = settings
    runner.state = BotState.SEARCHING
    runner.aligner = CameraAligner(camera, Rect(0, 0, 100, 100))
    runner.input = fake_input
    runner.thrower = ThrowController(fake_input, capture_config)
    runner._camera_keys_holding = set()
    return runner


def test_capture_step_holds_ball_and_aims_when_target_is_off_center() -> None:
    runner = make_runner()
    target = Detection("target_pet", 0.9, Rect(80, 5, 10, 10))

    runner._step_capture(target)

    assert runner.state == BotState.ALIGNING
    assert runner.input.events == [
        ("key_down", "right"),
        ("key_down", "up"),
    ]


def test_capture_step_holds_aim_when_target_is_centered() -> None:
    runner = make_runner()
    target = Detection("target_pet", 0.9, Rect(45, 45, 10, 10))

    runner._step_capture(target, now=10.0)

    assert runner.state == BotState.CAPTURING
    assert runner.input.events == [("mouse_down", "left")]


def test_capture_step_releases_after_hold_time() -> None:
    runner = make_runner()
    target = Detection("target_pet", 0.9, Rect(45, 45, 10, 10))

    runner._step_capture(target, now=10.0)
    runner._step_capture(target, now=10.4)

    assert runner.state == BotState.CAPTURING
    assert runner.input.events == [("mouse_down", "left"), ("mouse_up", "left")]


def test_capture_step_releases_camera_keys_when_target_is_missing() -> None:
    runner = make_runner()
    runner._sync_camera_keys({"left"})
    runner.input.events.clear()

    runner._step_capture(None)

    assert runner.state == BotState.SEARCHING
    assert runner.input.events == [("key_up", "left")]


def test_cleanup_input_release_ignores_release_errors() -> None:
    runner = make_runner()
    failing_input = FailingReleaseInput()
    runner.input = failing_input
    runner.thrower = ThrowController(failing_input, runner.settings.control.capture)
    runner._camera_keys_holding = {"left", "right"}

    runner._release_camera_keys(ignore_errors=True)
    runner._cancel_throw_hold(ignore_errors=True)

    assert runner._camera_keys_holding == set()
    assert failing_input.events == [
        ("key_up", "left"),
        ("key_up", "right"),
        ("mouse_up", "left"),
    ]
