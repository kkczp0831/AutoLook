# 连点器脚本：定位配置中的游戏窗口，并复用自动捕捉的投球按键逻辑。
# 不移动鼠标；用户可自行移动鼠标调整视角，按 Esc 可停止脚本。
from __future__ import annotations

import argparse
import time

from _bootstrap import add_src_to_path

add_src_to_path()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repeatedly throw balls inside the configured game window.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config.")
    parser.add_argument(
        "--interval",
        type=float,
        default=1,
        help="Seconds to wait after each throw before the next throw starts.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1009,
        help="Number of throws to send. Use 0 to throw until interrupted.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5,
        help="Seconds to wait before throwing starts.",
    )
    return parser


def _is_escape_pressed() -> bool:
    try:
        import win32api
    except ImportError:
        return False

    return bool(win32api.GetAsyncKeyState(0x1B) & 0x8000)


def main() -> None:
    args = build_parser().parse_args()
    if args.interval <= 0:
        raise ValueError("--interval must be greater than 0")
    if args.count < 0:
        raise ValueError("--count cannot be negative")
    if args.delay < 0:
        raise ValueError("--delay cannot be negative")

    from autolook.config import load_settings
    from autolook.bot.throw_controller import ThrowController
    from autolook.control import create_input_controller
    from autolook.window import activate_configured_window

    try:
        import pydirectinput
    except ImportError as exc:
        raise RuntimeError(
            "auto_clicker requires pydirectinput. Install it with: "
            "python -m pip install -e .[control]"
        ) from exc

    pydirectinput.PAUSE = 0
    settings = load_settings(args.config)
    activate_configured_window(settings)

    if args.delay > 0:
        print(
            f"Starting in {args.delay:.1f}s. "
            "Move the mouse into the game window and aim freely."
        )
        time.sleep(args.delay)

    capture_config = settings.control.capture.model_copy(
        update={"throw_cooldown_seconds": args.interval}
    )
    input_controller = create_input_controller(dry_run=False)
    thrower = ThrowController(input_controller, capture_config)

    target = "until interrupted" if args.count == 0 else str(args.count)
    print(
        "Throwing inside game window: "
        f"hold={capture_config.aim_hold_seconds:.3f}s, "
        f"cooldown={capture_config.throw_cooldown_seconds:.3f}s, count={target}."
    )
    print("Press Esc to stop.")

    throws = 0
    try:
        while args.count == 0 or throws < args.count:
            if _is_escape_pressed():
                print("Stopped because Esc was pressed.")
                break

            now = time.monotonic()
            thrown = thrower.throw_ball(now)
            if thrown:
                throws += 1
            time.sleep(settings.app.tick_interval_seconds)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        thrower.cancel_hold()

    print(f"Done. Sent {throws} throw(s).")


if __name__ == "__main__":
    main()
