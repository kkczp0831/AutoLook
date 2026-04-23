from __future__ import annotations

from autolook.control.input_controller import InputController, NullInputController


def create_input_controller(dry_run: bool) -> InputController:
    if dry_run:
        return NullInputController()

    from autolook.control.pydirectinput_controller import PyDirectInputController

    return PyDirectInputController()
