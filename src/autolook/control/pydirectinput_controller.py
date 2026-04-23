from __future__ import annotations

from autolook.control.input_controller import InputController


class PyDirectInputController(InputController):
    def __init__(self) -> None:
        try:
            import pydirectinput
        except ImportError as exc:
            raise RuntimeError(
                "PyDirectInput backend requires pydirectinput. Install it with: "
                "python -m pip install -e .[control]"
            ) from exc

        self._pydirectinput = pydirectinput
        self._pydirectinput.PAUSE = 0

    def move_mouse(self, dx: int, dy: int) -> None:
        self._pydirectinput.moveRel(int(dx), int(dy), duration=0, relative=True)

    def mouse_down(self, button: str) -> None:
        self._pydirectinput.mouseDown(button=button)

    def mouse_up(self, button: str) -> None:
        self._pydirectinput.mouseUp(button=button)

    def press_key(self, key: str) -> None:
        self._pydirectinput.press(key)

    def key_down(self, key: str) -> None:
        self._pydirectinput.keyDown(key)

    def key_up(self, key: str) -> None:
        self._pydirectinput.keyUp(key)
