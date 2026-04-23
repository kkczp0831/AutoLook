from autolook.control.factory import create_input_controller
from autolook.control.input_controller import NullInputController
from autolook.control.pydirectinput_controller import PyDirectInputController


def test_input_factory_returns_null_controller_for_dry_run() -> None:
    assert isinstance(create_input_controller(dry_run=True), NullInputController)


def test_input_factory_uses_pydirectinput_for_live_control() -> None:
    assert isinstance(create_input_controller(dry_run=False), PyDirectInputController)
