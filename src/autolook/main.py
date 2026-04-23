from __future__ import annotations

import argparse
from collections.abc import Sequence
import time

from autolook.config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AutoLook.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config.")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode.")
    parser.add_argument("--live", action="store_true", help="Enable real mouse/keyboard control.")
    parser.add_argument("--debug", action="store_true", help="Print detection diagnostics.")
    parser.add_argument(
        "--overlay-target",
        "--overlay",
        action="store_true",
        help="Draw a live transparent box around the selected target.",
    )
    parser.add_argument("--overlay-color", help="Target overlay border color in #RRGGBB format.")
    parser.add_argument(
        "--overlay-candidate-color",
        help="Non-selected detection overlay color in #RRGGBB format.",
    )
    parser.add_argument("--overlay-thickness", type=int, help="Target overlay border thickness.")
    parser.add_argument(
        "--max-runtime",
        type=float,
        help="Override maximum runtime in seconds. Keep this small for live tests.",
    )
    parser.add_argument(
        "--start-delay",
        type=float,
        default=0,
        help="Seconds to wait before starting. Useful for switching back to the game.",
    )
    parser.add_argument(
        "--focus-click",
        action="store_true",
        help="Click the configured game-region center before starting live control.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    settings = load_settings(args.config)
    if args.live and args.dry_run:
        raise ValueError("--live and --dry-run cannot be used together")
    if args.live:
        settings.app.dry_run = False
    if args.dry_run:
        settings.app.dry_run = True
    if args.debug:
        settings.app.debug = True
    if args.overlay_target:
        settings.app.overlay_target = True
    if args.overlay_color is not None:
        settings.app.overlay_color = args.overlay_color
    if args.overlay_candidate_color is not None:
        settings.app.overlay_candidate_color = args.overlay_candidate_color
    if args.overlay_thickness is not None:
        if args.overlay_thickness < 1:
            raise ValueError("--overlay-thickness must be at least 1")
        settings.app.overlay_thickness = args.overlay_thickness
    if args.max_runtime is not None:
        settings.app.max_runtime_seconds = args.max_runtime
    if args.start_delay < 0:
        raise ValueError("--start-delay cannot be negative")
    if args.start_delay > 0:
        print(f"Starting in {args.start_delay:.1f}s. Switch back to the game window now.")
        time.sleep(args.start_delay)
    if args.focus_click:
        if settings.app.dry_run:
            print("[dry-run] focus_click skipped because dry_run=True")
        else:
            import pydirectinput
            from autolook.window import activate_configured_window

            region = activate_configured_window(settings, debug=settings.app.debug)
            center_x = region.left + region.width // 2
            center_y = region.top + region.height // 2
            print(f"Focus click at ({center_x},{center_y})")
            pydirectinput.click(center_x, center_y, button="left")
            time.sleep(0.2)

    from autolook.bot.runner import BotRunner

    BotRunner(settings).run()


if __name__ == "__main__":
    main()
