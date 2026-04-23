from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    box: Rect

    @property
    def center(self) -> tuple[int, int]:
        return self.box.center


@dataclass(frozen=True)
class TargetLocation:
    target: Detection | None
    candidates: list[Detection]


class BotState(str, Enum):
    IDLE = "idle"
    SEARCHING = "searching"
    ALIGNING = "aligning"
    CAPTURING = "capturing"
    STOPPED = "stopped"
