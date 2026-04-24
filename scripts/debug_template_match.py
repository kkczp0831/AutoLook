# 模板匹配调试脚本：在截图或实时画面上运行模板匹配并输出最高分结果。
# 会保存带框标注的调试图片，方便检查模板质量和阈值设置。
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from _bootstrap import add_src_to_path

add_src_to_path()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Debug template matching on a screenshot.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config.")
    parser.add_argument("--image", help="Screenshot path. If omitted, grabs one live frame.")
    parser.add_argument("--top", type=int, default=10, help="Number of matches to print.")
    parser.add_argument(
        "--output-dir",
        default="data/screenshots/template_debug",
        help="Directory for annotated debug images.",
    )
    return parser


def main() -> None:
    import cv2
    import numpy as np

    from autolook.config import load_settings
    from autolook.vision.template_detector import TemplateDetector
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

    detector = TemplateDetector(settings.vision.template_dir)
    matches = sorted(detector.match(frame), key=lambda item: item.confidence, reverse=True)

    print(f"Loaded templates: {len(detector.templates)}")
    if not matches:
        print("No templates could be matched. Check template sizes and paths.")
        return

    print("Top matches:")
    for index, match in enumerate(matches[: args.top], start=1):
        print(
            f"{index:02d}. label={match.label} template={match.template_name} "
            f"score={match.confidence:.4f} "
            f"box=({match.box.left},{match.box.top},{match.box.width},{match.box.height})"
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated = frame.copy()
    for match in matches[: args.top]:
        color = (0, 255, 0) if match.confidence >= settings.targets.pets[0].min_confidence else (0, 180, 255)
        left, top = match.box.left, match.box.top
        right, bottom = left + match.box.width, top + match.box.height
        cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
        cv2.putText(
            annotated,
            f"{match.label} {match.confidence:.2f}",
            (left, max(20, top - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    filename = datetime.now().strftime("template_debug_%Y%m%d_%H%M%S.png")
    path = output_dir / filename
    ok, encoded = cv2.imencode(".png", annotated)
    if not ok:
        raise RuntimeError("Failed to encode debug image.")
    encoded.tofile(path)
    print(f"Saved debug image: {path}")


if __name__ == "__main__":
    main()
