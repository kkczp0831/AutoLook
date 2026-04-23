from autolook.config import Settings
from autolook.types import Rect
from autolook.window import resolve_capture_region


def test_resolve_capture_region_uses_static_region_when_auto_locate_disabled() -> None:
    settings = Settings()
    settings.window.auto_locate = False
    settings.window.region = Rect(left=10, top=20, width=300, height=200)

    assert resolve_capture_region(settings) == Rect(left=10, top=20, width=300, height=200)
