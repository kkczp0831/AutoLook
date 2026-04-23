from __future__ import annotations

import argparse

from _bootstrap import add_src_to_path

add_src_to_path()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List visible windows matching a title keyword.")
    parser.add_argument("--title", default="洛克王国", help="Title keyword to search for.")
    parser.add_argument(
        "--window-rect",
        action="store_true",
        help="Show full window rectangles instead of client-area rectangles.",
    )
    return parser


def main() -> None:
    from autolook.window.win32_window import Win32WindowManager

    args = build_parser().parse_args()
    manager = Win32WindowManager()

    try:
        info = manager.find_by_title(args.title, use_client_area=not args.window_rect)
    except RuntimeError as exc:
        print(exc)
        return

    region = info.region
    print(f"hwnd={info.hwnd}")
    print(f"title={info.title}")
    print(
        "region="
        f"left={region.left}, top={region.top}, width={region.width}, height={region.height}"
    )


if __name__ == "__main__":
    main()
