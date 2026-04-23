from autolook.bot.runner import BotRunner

from autolook.config import AppConfig, CameraConfig, ControlConfig, Settings


class FakeInput:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def key_down(self, key: str) -> None:
        self.events.append(("key_down", key))

    def key_up(self, key: str) -> None:
        self.events.append(("key_up", key))

    def mouse_down(self, button: str) -> None:
        self.events.append(("mouse_down", button))

    def mouse_up(self, button: str) -> None:
        self.events.append(("mouse_up", button))


def make_runner(camera: CameraConfig) -> BotRunner:
    runner = BotRunner.__new__(BotRunner)
    runner.settings = Settings(app=AppConfig(debug=False), control=ControlConfig(camera=camera))
    runner.input = FakeInput()
    runner._camera_keys_holding = set()
    return runner


def test_camera_key_mode_maps_delta_to_direction_keys() -> None:
    runner = make_runner(
        CameraConfig(
            key_left="a",
            key_right="d",
            key_up="w",
            key_down="s",
        )
    )

    assert runner._camera_keys_for_delta(-3, 4) == {"a", "s"}
    assert runner._camera_keys_for_delta(5, -2) == {"d", "w"}


def test_camera_key_mode_releases_keys_that_are_no_longer_needed() -> None:
    runner = make_runner(CameraConfig())

    runner._sync_camera_keys({"left"})
    runner._sync_camera_keys({"right"})
    runner._release_camera_keys()

    assert runner.input.events == [
        ("key_down", "left"),
        ("key_up", "left"),
        ("key_down", "right"),
        ("key_up", "right"),
    ]


def test_release_camera_control_releases_held_camera_key() -> None:
    runner = make_runner(CameraConfig())

    runner._sync_camera_keys({"left"})
    runner._release_camera_keys()

    assert runner.input.events == [("key_down", "left"), ("key_up", "left")]
    assert runner._camera_keys_holding == set()
