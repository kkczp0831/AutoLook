from autolook.bot.runner import BotRunner
from autolook.types import Detection, Rect, TargetLocation
from autolook.window.overlay import OverlayBox, Win32OverlayBorder, parse_hex_color


class FakeOverlay:
    def __init__(self) -> None:
        self.events: list[tuple[int, int, int, int]] = []
        self.hidden = False
        self.closed = False
        self.pumped = False

    def set_rect(self, left: int, top: int, width: int, height: int) -> None:
        self.events.append((left, top, width, height))
        self.hidden = False

    def hide(self) -> None:
        self.hidden = True

    def close(self) -> None:
        self.closed = True

    def pump(self) -> None:
        self.pumped = True


class FakeMultiOverlay(FakeOverlay):
    target_color_rgb = (0, 255, 0)
    candidate_color_rgb = (0, 191, 255)

    def __init__(self) -> None:
        super().__init__()
        self.box_events = []

    def set_boxes(self, left: int, top: int, width: int, height: int, boxes) -> None:
        self.box_events.append((left, top, width, height, boxes))
        self.hidden = False


def make_runner_with_overlay() -> tuple[BotRunner, FakeOverlay]:
    overlay = FakeOverlay()
    runner = BotRunner.__new__(BotRunner)
    runner.capture_region = Rect(left=100, top=200, width=800, height=600)
    runner._target_overlay = overlay
    return runner, overlay


def test_target_overlay_converts_capture_box_to_screen_coordinates() -> None:
    runner, overlay = make_runner_with_overlay()
    target = Detection("target_pet", 0.9, Rect(left=20, top=30, width=40, height=50))

    runner._update_overlay(target)

    assert overlay.events == [(120, 230, 40, 50)]
    assert not overlay.hidden


def test_target_overlay_draws_all_candidates_and_highlights_selected_target() -> None:
    overlay = FakeMultiOverlay()
    runner = BotRunner.__new__(BotRunner)
    runner.capture_region = Rect(left=100, top=200, width=800, height=600)
    runner._target_overlay = overlay
    selected = Detection("target_pet", 0.9, Rect(left=20, top=30, width=40, height=50))
    other = Detection("target_pet", 0.7, Rect(left=120, top=130, width=40, height=50))

    runner._update_overlay(TargetLocation(target=selected, candidates=[other, selected]))

    assert len(overlay.box_events) == 1
    left, top, width, height, boxes = overlay.box_events[0]
    assert (left, top, width, height) == (100, 200, 800, 600)
    assert [(box.left, box.top, box.label, box.color_rgb) for box in boxes] == [
        (120, 130, "0.70", overlay.candidate_color_rgb),
        (20, 30, "0.90", overlay.target_color_rgb),
    ]


def test_target_overlay_hides_when_target_is_missing() -> None:
    runner, overlay = make_runner_with_overlay()

    runner._update_overlay(None)

    assert overlay.hidden


def test_target_overlay_pump_and_close_are_noops_without_overlay() -> None:
    runner = BotRunner.__new__(BotRunner)
    runner._target_overlay = None

    runner._pump_overlay()
    runner._close_overlay()

    assert runner._target_overlay is None


def test_target_overlay_parses_hex_color() -> None:
    assert parse_hex_color("#12A0ff") == (18, 160, 255)


def test_overlay_erase_background_uses_window_proc_signature() -> None:
    overlay = Win32OverlayBorder.__new__(Win32OverlayBorder)

    assert overlay._on_erase_background(0, 0, 0, 0) == 1


def test_overlay_draw_label_uses_pywin32_draw_text() -> None:
    class FakeWin32Gui:
        def __init__(self) -> None:
            self.draw_text_calls = []

        def SetBkMode(self, *args):
            return "old-bk"

        def SetTextColor(self, *args):
            return "old-color"

        def DrawText(self, *args):
            self.draw_text_calls.append(args)

    class FakeWin32Con:
        TRANSPARENT = 1
        DT_LEFT = 0x0000
        DT_TOP = 0x0000
        DT_SINGLELINE = 0x0020
        DT_NOCLIP = 0x0100

    fake_win32gui = FakeWin32Gui()
    overlay = Win32OverlayBorder.__new__(Win32OverlayBorder)
    overlay.win32gui = fake_win32gui
    overlay.win32con = FakeWin32Con
    overlay._width = 300

    overlay._draw_label(
        "hdc",
        OverlayBox(
            left=20,
            top=30,
            width=40,
            height=50,
            label="0.90",
            color_rgb=(0, 255, 0),
        ),
        123,
    )

    expected_flags = FakeWin32Con.DT_SINGLELINE | FakeWin32Con.DT_NOCLIP
    assert fake_win32gui.draw_text_calls == [
        ("hdc", "0.90", 4, (20, 12, 100, 30), expected_flags)
    ]
