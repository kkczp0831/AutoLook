from __future__ import annotations

from autolook.config import Settings
from autolook.types import Rect
from autolook.window.win32_window import Win32WindowManager


def resolve_capture_region(settings: Settings, activate: bool = False, debug: bool = False) -> Rect:
    if not settings.window.auto_locate:
        return settings.window.region

    manager = Win32WindowManager()
    info = manager.find_by_title(
        settings.window.title_keyword,
        use_client_area=settings.window.use_client_area,
    )
    if activate or settings.window.activate_before_start:
        manager.activate(info.hwnd)

    if debug:
        print(
            "[debug] window "
            f"hwnd={info.hwnd} title={info.title!r} "
            f"region=({info.region.left},{info.region.top},{info.region.width},{info.region.height})"
        )

    return info.region


def activate_configured_window(settings: Settings, debug: bool = False) -> Rect:
    return resolve_capture_region(settings, activate=True, debug=debug)
