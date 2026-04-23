from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from autolook.types import Rect


class AppConfig(BaseModel):
    name: str = "AutoLook"
    dry_run: bool = True
    debug: bool = False
    overlay_target: bool = False
    overlay_color: str = "#00FF00"
    overlay_candidate_color: str = "#00BFFF"
    overlay_thickness: int = 3
    debug_interval_seconds: float = 1.0
    tick_interval_seconds: float = 0.1
    max_runtime_seconds: float = 0


class WindowConfig(BaseModel):
    title_keyword: str = ""
    auto_locate: bool = True
    use_client_area: bool = True
    activate_before_start: bool = False
    region: Rect = Field(default_factory=lambda: Rect(left=0, top=0, width=1280, height=720))


class TargetPetConfig(BaseModel):
    name: str
    enabled: bool = True
    detector_label: str
    min_confidence: float = 0.65


class TargetsConfig(BaseModel):
    pets: list[TargetPetConfig] = Field(default_factory=list)


class VisionInputSize(BaseModel):
    width: int = 640
    height: int = 640


class TrackingConfig(BaseModel):
    enabled: bool = True
    detector_interval_frames: int = 10
    max_stale_frames: int = 5
    search_margin_px: int = 160
    min_confidence: float = 0.55
    template_padding_px: int = 12


class VisionConfig(BaseModel):
    backend: str = "template"
    template_dir: Path = Path("data/templates")
    template_match_threshold: float = 0.0
    model_path: Path = Path("data/models/pet_detector.onnx")
    yolo_confidence_threshold: float = 0.0
    input_size: VisionInputSize = Field(default_factory=VisionInputSize)
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    debug_screenshots: bool = False


class CameraConfig(BaseModel):
    center_tolerance_px: int = 48
    key_left: str = "left"
    key_right: str = "right"
    key_up: str = "up"
    key_down: str = "down"


class CaptureControlConfig(BaseModel):
    ball_button: str = "left"
    aim_hold_seconds: float = Field(default=0.35, ge=0)
    throw_cooldown_seconds: float = Field(default=1.0, ge=0)


class ControlConfig(BaseModel):
    camera: CameraConfig = Field(default_factory=CameraConfig)
    capture: CaptureControlConfig = Field(default_factory=CaptureControlConfig)


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    window: WindowConfig = Field(default_factory=WindowConfig)
    targets: TargetsConfig = Field(default_factory=TargetsConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    control: ControlConfig = Field(default_factory=ControlConfig)


def load_settings(path: str | Path = "config/default.yaml") -> Settings:
    config_path = Path(path)
    data: dict[str, Any] = {}
    if config_path.exists():
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return Settings.model_validate(data)
