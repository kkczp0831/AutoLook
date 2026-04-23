from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect screen samples for dataset building.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config.")
    parser.add_argument(
        "--output-dir",
        default="data/datasets/raw",
        help="Directory where screenshots will be saved.",
    )
    parser.add_argument("--prefix", default="sample", help="Filename prefix.")
    parser.add_argument("--count", type=int, default=20, help="Number of screenshots to capture.")
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Seconds to wait between screenshots.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Seconds to wait before the first screenshot. Useful for switching back to the game.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.count < 1:
        raise ValueError("--count must be at least 1")
    if args.interval < 0:
        raise ValueError("--interval cannot be negative")
    if args.delay < 0:
        raise ValueError("--delay cannot be negative")

    import cv2

    from autolook.capture import MssFrameSource
    from autolook.config import load_settings
    from autolook.window import resolve_capture_region

    settings = load_settings(args.config)
    region = resolve_capture_region(settings)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.delay > 0:
        print(f"Starting in {args.delay:.1f}s. Switch back to the game window now.")
        time.sleep(args.delay)

    frame_source = MssFrameSource(region)
    print(
        "Collecting samples: "
        f"count={args.count}, interval={args.interval:.2f}s, output_dir={output_dir}, "
        f"region=({region.left},{region.top},{region.width},{region.height})"
    )

    saved = 0
    try:
        for index in range(1, args.count + 1):
            frame = frame_source.grab()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{args.prefix}_{timestamp}_{index:04d}.png"
            path = output_dir / filename
            if not cv2.imwrite(str(path), frame):
                raise RuntimeError(f"Failed to save screenshot: {path}")

            saved += 1
            print(f"[{index}/{args.count}] Saved sample: {path}")

            if index < args.count and args.interval > 0:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    print(f"Done. Saved {saved} screenshot(s).")


if __name__ == "__main__":
    main()
