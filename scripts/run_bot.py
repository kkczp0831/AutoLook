from __future__ import annotations

import sys

from _bootstrap import add_src_to_path

add_src_to_path()

from autolook.main import main


RUN_ARGS = [
    "--live",
    "--debug",
    "--overlay-target",
    "--overlay-color",
    "#00FF00",
    "--overlay-candidate-color",
    "#00BFFF",
    "--focus-click",
    "--start-delay",
    "5",
    "--max-runtime",
    "120",
]


def effective_args(cli_args: list[str]) -> list[str]:
    run_args = list(RUN_ARGS)
    if "--dry-run" in cli_args:
        run_args = [arg for arg in run_args if arg != "--live"]
    return [*run_args, *cli_args]


if __name__ == "__main__":
    main(effective_args(sys.argv[1:]))
