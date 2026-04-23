from __future__ import annotations

from autolook.config import VisionConfig
from autolook.vision.detector import Detector
from autolook.vision.onnx_detector import OnnxDetector
from autolook.vision.template_detector import TemplateDetector
from autolook.vision.yolo_detector import YoloDetector


def create_detector(config: VisionConfig) -> Detector:
    if config.backend == "template":
        return TemplateDetector(config.template_dir, threshold=config.template_match_threshold)
    if config.backend == "onnx":
        return OnnxDetector(config.model_path)
    if config.backend == "yolo":
        return YoloDetector(config)
    raise ValueError(f"Unsupported vision backend: {config.backend}")
