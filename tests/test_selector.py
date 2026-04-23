from autolook.bot.selector import TargetSelector
from autolook.config import TargetPetConfig, TargetsConfig
from autolook.types import Detection, Rect


def test_selector_returns_best_enabled_target() -> None:
    selector = TargetSelector(
        TargetsConfig(
            pets=[
                TargetPetConfig(name="目标宠物", detector_label="target_pet", min_confidence=0.6)
            ]
        )
    )
    detections = [
        Detection("other", 0.99, Rect(0, 0, 10, 10)),
        Detection("target_pet", 0.75, Rect(0, 0, 10, 10)),
        Detection("target_pet", 0.8, Rect(0, 0, 10, 10)),
    ]

    assert selector.choose(detections) == detections[2]


def test_selector_returns_all_enabled_candidates_above_threshold() -> None:
    selector = TargetSelector(
        TargetsConfig(
            pets=[TargetPetConfig(name="target", detector_label="target_pet", min_confidence=0.6)]
        )
    )
    detections = [
        Detection("target_pet", 0.59, Rect(0, 0, 10, 10)),
        Detection("target_pet", 0.75, Rect(10, 0, 10, 10)),
        Detection("other", 0.99, Rect(20, 0, 10, 10)),
        Detection("target_pet", 0.8, Rect(30, 0, 10, 10)),
    ]

    assert selector.candidates(detections) == [detections[1], detections[3]]
