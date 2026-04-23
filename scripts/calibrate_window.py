from __future__ import annotations

from _bootstrap import add_src_to_path

add_src_to_path()

from autolook.config import load_settings
from autolook.window import resolve_capture_region


def main() -> None:
    settings = load_settings()
    region = resolve_capture_region(settings, debug=True)
    print(
        "Current capture region: "
        f"left={region.left}, top={region.top}, width={region.width}, height={region.height}"
    )
    print("Update config/default.yaml after measuring the game window region.")


if __name__ == "__main__":
    main()
