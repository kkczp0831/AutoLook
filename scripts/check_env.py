# 环境检查脚本：检查运行 AutoLook 所需的 Python 依赖是否已安装。
# 会根据当前视觉后端提示应安装的 control/yolo 等依赖组合。
from __future__ import annotations

from _bootstrap import add_src_to_path

add_src_to_path()


REQUIRED_MODULES = {
    "cv2": "opencv-python",
    "mss": "mss",
    "numpy": "numpy",
    "pydirectinput": "pydirectinput",
    "pydantic": "pydantic",
    "win32gui": "pywin32",
    "yaml": "PyYAML",
}


def main() -> None:
    from autolook.config import load_settings

    missing: list[str] = []

    for module_name, package_name in REQUIRED_MODULES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    settings = load_settings()
    if settings.vision.backend == "yolo":
        try:
            __import__("ultralytics")
        except ImportError:
            missing.append("ultralytics")

    if not missing:
        print("Environment looks good. All required runtime dependencies are installed.")
        return

    print("Missing runtime dependencies:")
    for package_name in missing:
        print(f"  - {package_name}")
    print()
    print("Install them with:")
    if settings.vision.backend == "yolo":
        print("  python -m pip install -e .[control,yolo]")
    else:
        print("  python -m pip install -e .[control]")
    print()
    print("Or install only the missing packages:")
    print(f"  python -m pip install {' '.join(missing)}")


if __name__ == "__main__":
    main()
