from __future__ import annotations

from dataclasses import dataclass
import importlib

from autolook.window.win32_window import configure_process_dpi_awareness


@dataclass(frozen=True)
class OverlayBox:
    left: int
    top: int
    width: int
    height: int
    label: str
    color_rgb: tuple[int, int, int]


class Win32OverlayBorder:
    def __init__(
        self,
        color_rgb: tuple[int, int, int],
        thickness: int,
        candidate_color_rgb: tuple[int, int, int] | None = None,
    ) -> None:
        configure_process_dpi_awareness()
        try:
            win32api = importlib.import_module("win32api")
            win32con = importlib.import_module("win32con")
            win32gui = importlib.import_module("win32gui")
        except ImportError as exc:
            raise RuntimeError(
                "pywin32 is required for target overlay. Install with: "
                "python -m pip install -e .[control]"
            ) from exc

        self.win32api = win32api
        self.win32con = win32con
        self.win32gui = win32gui

        self._class_name = "AutoLookTargetOverlay"
        self._instance = win32api.GetModuleHandle(None)
        self._hwnd: int | None = None
        self._thickness = max(1, int(thickness))
        self._color_rgb = color_rgb
        self._candidate_color_rgb = candidate_color_rgb or color_rgb
        self._width = 0
        self._height = 0
        self._items: list[OverlayBox] = []

        self._register_class()
        self._create_window()

    @classmethod
    def from_hex_color(
        cls,
        color: str,
        thickness: int,
        candidate_color: str | None = None,
    ) -> Win32OverlayBorder:
        return cls(
            color_rgb=parse_hex_color(color),
            thickness=thickness,
            candidate_color_rgb=parse_hex_color(candidate_color) if candidate_color else None,
        )

    @property
    def target_color_rgb(self) -> tuple[int, int, int]:
        return self._color_rgb

    @property
    def candidate_color_rgb(self) -> tuple[int, int, int]:
        return self._candidate_color_rgb

    def _register_class(self) -> None:
        wnd_class = self.win32gui.WNDCLASS()
        wnd_class.hInstance = self._instance
        wnd_class.lpszClassName = self._class_name
        wnd_class.lpfnWndProc = {
            self.win32con.WM_PAINT: self._on_paint,
            self.win32con.WM_ERASEBKGND: self._on_erase_background,
            self.win32con.WM_DESTROY: self._on_destroy,
        }

        try:
            self.win32gui.RegisterClass(wnd_class)
        except self.win32gui.error as exc:
            if exc.winerror != 1410:
                raise

    def _create_window(self) -> None:
        ex_style = (
            self.win32con.WS_EX_LAYERED
            | self.win32con.WS_EX_TRANSPARENT
            | self.win32con.WS_EX_TOOLWINDOW
            | self.win32con.WS_EX_TOPMOST
            | self.win32con.WS_EX_NOACTIVATE
        )

        self._hwnd = self.win32gui.CreateWindowEx(
            ex_style,
            self._class_name,
            "",
            self.win32con.WS_POPUP,
            0,
            0,
            0,
            0,
            0,
            0,
            self._instance,
            None,
        )

        self.win32gui.SetLayeredWindowAttributes(
            self._hwnd,
            self.win32api.RGB(0, 0, 0),
            0,
            self.win32con.LWA_COLORKEY,
        )

    def set_rect(self, left: int, top: int, width: int, height: int) -> None:
        self.set_boxes(
            left,
            top,
            width,
            height,
            [
                OverlayBox(
                    left=0,
                    top=0,
                    width=width,
                    height=height,
                    label="",
                    color_rgb=self._color_rgb,
                )
            ],
        )

    def set_boxes(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
        boxes: list[OverlayBox],
    ) -> None:
        if self._hwnd is None:
            return

        self._width = max(0, int(width))
        self._height = max(0, int(height))
        self._items = list(boxes)

        if self._width <= 0 or self._height <= 0 or not self._items:
            self.win32gui.ShowWindow(self._hwnd, self.win32con.SW_HIDE)
            return

        self.win32gui.SetWindowPos(
            self._hwnd,
            self.win32con.HWND_TOPMOST,
            int(left),
            int(top),
            self._width,
            self._height,
            self.win32con.SWP_NOACTIVATE,
        )
        self.win32gui.ShowWindow(self._hwnd, self.win32con.SW_SHOWNOACTIVATE)
        self.win32gui.InvalidateRect(self._hwnd, None, True)

    def hide(self) -> None:
        self.set_rect(0, 0, 0, 0)

    def pump(self) -> None:
        self.win32gui.PumpWaitingMessages()

    def close(self) -> None:
        if self._hwnd is not None:
            self.win32gui.DestroyWindow(self._hwnd)
            self._hwnd = None

    def _on_erase_background(
        self,
        _hwnd: int,
        _msg: int,
        _wparam: int,
        _lparam: int,
    ) -> int:
        return 1

    def _on_paint(self, hwnd: int, _msg: int, _wparam: int, _lparam: int) -> int:
        hdc, paint_struct = self.win32gui.BeginPaint(hwnd)
        try:
            rect = (0, 0, self._width, self._height)
            brush = self.win32gui.GetStockObject(self.win32con.BLACK_BRUSH)
            self.win32gui.FillRect(hdc, rect, brush)

            if self._width > 0 and self._height > 0:
                for item in self._items:
                    self._draw_box(hdc, item)
        finally:
            self.win32gui.EndPaint(hwnd, paint_struct)

        return 0

    def _draw_box(self, hdc, item: OverlayBox) -> None:
        if item.width <= 0 or item.height <= 0:
            return

        color = self.win32api.RGB(*item.color_rgb)
        pen = self.win32gui.CreatePen(self.win32con.PS_SOLID, self._thickness, color)
        old_pen = self.win32gui.SelectObject(hdc, pen)
        old_brush = self.win32gui.SelectObject(
            hdc, self.win32gui.GetStockObject(self.win32con.HOLLOW_BRUSH)
        )
        try:
            inset = max(0, self._thickness // 2)
            left = int(item.left) + inset
            top = int(item.top) + inset
            right = int(item.left + item.width) - inset
            bottom = int(item.top + item.height) - inset
            self.win32gui.Rectangle(
                hdc,
                left,
                top,
                max(left + 1, right),
                max(top + 1, bottom),
            )
            self._draw_label(hdc, item, color)
        finally:
            self.win32gui.SelectObject(hdc, old_brush)
            self.win32gui.SelectObject(hdc, old_pen)
            self.win32gui.DeleteObject(pen)

    def _draw_label(self, hdc, item: OverlayBox, color: int) -> None:
        if not item.label:
            return

        old_bk_mode = self.win32gui.SetBkMode(hdc, self.win32con.TRANSPARENT)
        old_text_color = self.win32gui.SetTextColor(hdc, color)
        try:
            text_left = max(0, min(int(item.left), max(0, self._width - 1)))
            text_top = int(item.top) - 18
            if text_top < 0:
                text_top = int(item.top) + 2
            self.win32gui.DrawText(
                hdc,
                item.label,
                len(item.label),
                (text_left, text_top, text_left + 80, text_top + 18),
                (
                    self.win32con.DT_LEFT
                    | self.win32con.DT_TOP
                    | self.win32con.DT_SINGLELINE
                    | self.win32con.DT_NOCLIP
                ),
            )
        finally:
            self.win32gui.SetTextColor(hdc, old_text_color)
            self.win32gui.SetBkMode(hdc, old_bk_mode)

    def _on_destroy(self, _hwnd: int, _msg: int, _wparam: int, _lparam: int) -> int:
        return 0


def parse_hex_color(value: str) -> tuple[int, int, int]:
    color = value.strip()
    if color.startswith("#"):
        color = color[1:]

    if len(color) != 6:
        raise ValueError(f"Invalid color: {value!r}. Expected #RRGGBB.")

    try:
        red = int(color[0:2], 16)
        green = int(color[2:4], 16)
        blue = int(color[4:6], 16)
    except ValueError as exc:
        raise ValueError(f"Invalid color: {value!r}. Expected hex digits.") from exc

    return red, green, blue
