# 脚本辅助模块：把项目的 src 目录加入 Python 搜索路径。
# 供 scripts 目录下其它脚本导入项目代码使用，通常不需要单独运行。
from __future__ import annotations

import sys
from pathlib import Path


def add_src_to_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
