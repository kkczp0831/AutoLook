from __future__ import annotations

from typing import Protocol


class InputController(Protocol):
    def move_mouse(self, dx: int, dy: int) -> None:
        """Move aim/camera by a relative amount."""

    def mouse_down(self, button: str) -> None:
        """Hold a mouse button."""

    def mouse_up(self, button: str) -> None:
        """Release a mouse button."""

    def press_key(self, key: str) -> None:
        """Press a key once."""

    def key_down(self, key: str) -> None:
        """Hold a keyboard key."""

    def key_up(self, key: str) -> None:
        """Release a keyboard key."""


class NullInputController:
    def move_mouse(self, dx: int, dy: int) -> None:
        print(f"[dry-run] move_mouse dx={dx} dy={dy}")

    def mouse_down(self, button: str) -> None:
        print(f"[dry-run] mouse_down button={button}")

    def mouse_up(self, button: str) -> None:
        print(f"[dry-run] mouse_up button={button}")

    def press_key(self, key: str) -> None:
        print(f"[dry-run] press_key key={key}")

    def key_down(self, key: str) -> None:
        print(f"[dry-run] key_down key={key}")

    def key_up(self, key: str) -> None:
        print(f"[dry-run] key_up key={key}")
