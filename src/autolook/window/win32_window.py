from __future__ import annotations

import ctypes
from dataclasses import dataclass
from ctypes import wintypes

from autolook.types import Rect


WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_DPI_AWARENESS_CONFIGURED = False


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    title: str
    region: Rect


def configure_process_dpi_awareness() -> None:
    global _DPI_AWARENESS_CONFIGURED

    if _DPI_AWARENESS_CONFIGURED:
        return

    user32 = ctypes.windll.user32
    try:
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            _DPI_AWARENESS_CONFIGURED = True
            return
    except (AttributeError, OSError, ValueError):
        pass

    try:
        shcore = ctypes.windll.shcore
        result = shcore.SetProcessDpiAwareness(2)
        if result in (0, -2147024891):
            _DPI_AWARENESS_CONFIGURED = True
            return
    except (AttributeError, OSError):
        pass

    try:
        user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass

    _DPI_AWARENESS_CONFIGURED = True


class Win32WindowManager:
    def __init__(self) -> None:
        configure_process_dpi_awareness()
        self._user32 = ctypes.windll.user32
        self._configure_function_signatures()

    def _configure_function_signatures(self) -> None:
        self._user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
        self._user32.EnumWindows.restype = wintypes.BOOL
        self._user32.IsWindowVisible.argtypes = [wintypes.HWND]
        self._user32.IsWindowVisible.restype = wintypes.BOOL
        self._user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self._user32.GetWindowTextLengthW.restype = ctypes.c_int
        self._user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        ]
        self._user32.GetWindowTextW.restype = ctypes.c_int
        self._user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self._user32.GetClientRect.restype = wintypes.BOOL
        self._user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
        self._user32.ClientToScreen.restype = wintypes.BOOL
        self._user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self._user32.GetWindowRect.restype = wintypes.BOOL
        self._user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self._user32.ShowWindow.restype = wintypes.BOOL
        self._user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        self._user32.SetForegroundWindow.restype = wintypes.BOOL

    def find_by_title(self, title_keyword: str, use_client_area: bool = True) -> WindowInfo:
        keyword = title_keyword.lower()
        matches: list[tuple[int, str]] = []

        def enum_handler(hwnd: int, _: int) -> int:
            try:
                if not self._user32.IsWindowVisible(hwnd):
                    return 1
                title = self._window_text(hwnd)
                if title and keyword in title.lower():
                    matches.append((hwnd, title))
            except OSError:
                return 1
            return 1

        callback = WNDENUMPROC(enum_handler)
        if not self._user32.EnumWindows(callback, 0):
            raise ctypes.WinError()
        if not matches:
            raise RuntimeError(f"No visible window found containing title: {title_keyword!r}")

        hwnd, title = matches[0]
        return WindowInfo(
            hwnd=hwnd,
            title=title,
            region=self.get_region(hwnd, use_client_area=use_client_area),
        )

    def get_region(self, hwnd: int, use_client_area: bool = True) -> Rect:
        if use_client_area:
            rect = wintypes.RECT()
            if not self._user32.GetClientRect(hwnd, ctypes.byref(rect)):
                raise ctypes.WinError()
            top_left = wintypes.POINT(rect.left, rect.top)
            bottom_right = wintypes.POINT(rect.right, rect.bottom)
            if not self._user32.ClientToScreen(hwnd, ctypes.byref(top_left)):
                raise ctypes.WinError()
            if not self._user32.ClientToScreen(hwnd, ctypes.byref(bottom_right)):
                raise ctypes.WinError()
            screen_left, screen_top = top_left.x, top_left.y
            screen_right, screen_bottom = bottom_right.x, bottom_right.y
        else:
            rect = wintypes.RECT()
            if not self._user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                raise ctypes.WinError()
            screen_left, screen_top = rect.left, rect.top
            screen_right, screen_bottom = rect.right, rect.bottom

        return Rect(
            left=int(screen_left),
            top=int(screen_top),
            width=max(0, int(screen_right - screen_left)),
            height=max(0, int(screen_bottom - screen_top)),
        )

    def activate(self, hwnd: int) -> None:
        self._user32.ShowWindow(hwnd, 9)
        if not self._user32.SetForegroundWindow(hwnd):
            raise ctypes.WinError()

    def _window_text(self, hwnd: int) -> str:
        length = self._user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buffer = ctypes.create_unicode_buffer(length + 1)
        copied = self._user32.GetWindowTextW(hwnd, buffer, length + 1)
        if copied <= 0:
            return ""
        return buffer.value
