from autolook.bot.throw_controller import ThrowController
from autolook.config import CaptureControlConfig


class FakeInput:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def move_mouse(self, dx: int, dy: int) -> None:
        self.events.append(("move_mouse", f"{dx},{dy}"))

    def mouse_down(self, button: str) -> None:
        self.events.append(("mouse_down", button))

    def mouse_up(self, button: str) -> None:
        self.events.append(("mouse_up", button))

    def press_key(self, key: str) -> None:
        self.events.append(("press_key", key))

    def key_down(self, key: str) -> None:
        self.events.append(("key_down", key))

    def key_up(self, key: str) -> None:
        self.events.append(("key_up", key))


def test_throw_controller_holds_then_releases_ball() -> None:
    fake_input = FakeInput()
    thrower = ThrowController(fake_input, CaptureControlConfig(aim_hold_seconds=0.5))

    thrown = thrower.throw_ball(now=10.0)

    assert not thrown
    assert thrower.is_holding
    assert fake_input.events == [("mouse_down", "left")]

    thrown = thrower.throw_ball(now=10.4)

    assert not thrown
    assert fake_input.events == [("mouse_down", "left")]

    thrown = thrower.throw_ball(now=10.5)

    assert thrown
    assert not thrower.is_holding
    assert fake_input.events == [("mouse_down", "left"), ("mouse_up", "left")]


def test_throw_controller_respects_cooldown_after_release() -> None:
    fake_input = FakeInput()
    thrower = ThrowController(
        fake_input,
        CaptureControlConfig(aim_hold_seconds=0, throw_cooldown_seconds=1.0),
    )

    assert thrower.throw_ball(now=10.0)
    assert not thrower.throw_ball(now=10.5)
    assert thrower.throw_ball(now=11.0)

    assert fake_input.events == [
        ("mouse_down", "left"),
        ("mouse_up", "left"),
        ("mouse_down", "left"),
        ("mouse_up", "left"),
    ]


def test_throw_controller_cancel_releases_button() -> None:
    fake_input = FakeInput()
    thrower = ThrowController(fake_input, CaptureControlConfig())

    thrower.cancel_hold()

    assert fake_input.events == [("mouse_up", "left")]
