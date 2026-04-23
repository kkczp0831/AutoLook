from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Debug target aiming without moving the mouse.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config.")
    parser.add_argument("--image", help="Screenshot path. If omitted, grabs one live frame.")
    parser.add_argument(
        "--output-dir",
        default="data/screenshots/aim_debug",
        help="Directory for annotated debug images.",
    )
    parser.add_argument(
        "--include-below-threshold",
        action="store_true",
        help="Use the best raw template match even if it is below min_confidence.",
    )
    return parser


def main() -> None:
    import cv2
    import numpy as np

    from autolook.bot.selector import TargetSelector
    from autolook.config import load_settings
    from autolook.control.camera import CameraAligner
    from autolook.types import Detection
    from autolook.vision import create_detector
    from autolook.window import resolve_capture_region

    args = build_parser().parse_args()
    settings = load_settings(args.config)
    region = resolve_capture_region(settings)

    if args.image:
        frame = cv2.imdecode(np.fromfile(args.image, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise RuntimeError(f"Failed to read image: {args.image}")
    else:
        from autolook.capture import MssFrameSource

        frame = MssFrameSource(region).grab()

    detector = create_detector(settings.vision)
    selector = TargetSelector(settings.targets)
    detections = detector.detect(frame)
    target = selector.choose(detections)

    if target is None and args.include_below_threshold:
        match = getattr(detector, "match", None)
        if match is not None:
            raw_matches = sorted(match(frame), key=lambda item: item.confidence, reverse=True)
            if raw_matches:
                best = raw_matches[0]
                target = Detection(best.label, best.confidence, best.box)

    aligner = CameraAligner(settings.control.camera, region)
    annotated = frame.copy()
    center_x, center_y = region.width // 2, region.height // 2
    tolerance = settings.control.camera.center_tolerance_px

    cv2.drawMarker(
        annotated,
        (center_x, center_y),
        (255, 255, 255),
        markerType=cv2.MARKER_CROSS,
        markerSize=36,
        thickness=2,
    )
    cv2.rectangle(
        annotated,
        (center_x - tolerance, center_y - tolerance),
        (center_x + tolerance, center_y + tolerance),
        (255, 255, 0),
        2,
    )

    if target is None:
        print("No target selected. Try --include-below-threshold or lower min_confidence.")
        _save_debug_image(annotated, args.output_dir)
        return

    dx, dy = aligner.alignment_delta(target)
    target_x, target_y = target.center
    error_x = target_x - center_x
    error_y = target_y - center_y
    is_centered = aligner.is_centered(target)

    left, top = target.box.left, target.box.top
    right, bottom = left + target.box.width, top + target.box.height
    color = (0, 255, 0) if is_centered else (0, 120, 255)
    cv2.rectangle(annotated, (left, top), (right, bottom), color, 3)
    cv2.circle(annotated, (target_x, target_y), 8, (0, 0, 255), -1)
    cv2.line(annotated, (center_x, center_y), (target_x, target_y), (0, 0, 255), 2)
    cv2.arrowedLine(
        annotated,
        (center_x, center_y),
        (center_x + dx, center_y + dy),
        (0, 255, 255),
        3,
        tipLength=0.25,
    )
    cv2.putText(
        annotated,
        f"{target.label} score={target.confidence:.3f}",
        (left, max(28, top - 12)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
    )
    cv2.putText(
        annotated,
        f"error=({error_x},{error_y}) move=({dx},{dy}) centered={is_centered}",
        (24, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2,
    )

    print(
        f"target label={target.label} score={target.confidence:.4f} "
        f"center=({target_x},{target_y}) screen_center=({center_x},{center_y}) "
        f"error=({error_x},{error_y}) move=({dx},{dy}) centered={is_centered}"
    )
    _save_debug_image(annotated, args.output_dir)


def _save_debug_image(frame, output_dir: str) -> None:
    import cv2

    path_dir = Path(output_dir)
    path_dir.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("aim_debug_%Y%m%d_%H%M%S.png")
    path = path_dir / filename
    ok, encoded = cv2.imencode(".png", frame)
    if not ok:
        raise RuntimeError("Failed to encode debug image.")
    encoded.tofile(path)
    print(f"Saved debug image: {path}")


if __name__ == "__main__":
    main()
