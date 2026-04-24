# 连点器脚本：按指定间隔频繁点击鼠标左键。
# 可通过 --interval 设置点击间隔，通过 --count 限制点击次数。
from __future__ import annotations

import argparse
import time


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repeatedly click the left mouse button.")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Seconds to wait between left-clicks.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of clicks to send. Use 0 to click until interrupted.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Seconds to wait before clicking starts.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.interval <= 0:
        raise ValueError("--interval must be greater than 0")
    if args.count < 0:
        raise ValueError("--count cannot be negative")
    if args.delay < 0:
        raise ValueError("--delay cannot be negative")

    try:
        import pydirectinput
    except ImportError as exc:
        raise RuntimeError(
            "auto_clicker requires pydirectinput. Install it with: "
            "python -m pip install -e .[control]"
        ) from exc

    pydirectinput.PAUSE = 0

    if args.delay > 0:
        print(f"Starting in {args.delay:.1f}s. Switch to the target window now.")
        time.sleep(args.delay)

    target = "until interrupted" if args.count == 0 else str(args.count)
    print(f"Clicking left mouse button every {args.interval:.3f}s, count={target}.")

    clicks = 0
    try:
        while args.count == 0 or clicks < args.count:
            pydirectinput.click(button="left")
            clicks += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    print(f"Done. Sent {clicks} click(s).")


if __name__ == "__main__":
    main()
