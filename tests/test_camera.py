from autolook.config import CameraConfig
from autolook.control.camera import CameraAligner
from autolook.types import Detection, Rect


def test_centered_detection_needs_no_camera_movement() -> None:
    aligner = CameraAligner(CameraConfig(center_tolerance_px=20), Rect(0, 0, 100, 100))
    detection = Detection("target_pet", 0.9, Rect(45, 45, 10, 10))

    assert aligner.alignment_delta(detection) == (0, 0)
    assert aligner.is_centered(detection)


def test_off_center_detection_returns_clamped_delta() -> None:
    aligner = CameraAligner(CameraConfig(center_tolerance_px=5), Rect(0, 0, 100, 100))
    detection = Detection("target_pet", 0.9, Rect(90, 90, 10, 10))

    assert aligner.alignment_delta(detection) == (1, 1)


def test_camera_aligner_can_sync_to_actual_frame_size() -> None:
    aligner = CameraAligner(CameraConfig(center_tolerance_px=5), Rect(0, 0, 200, 200))
    aligner.set_viewport_size(100, 100)
    detection = Detection("target_pet", 0.9, Rect(45, 45, 10, 10))

    assert aligner.is_centered(detection)
