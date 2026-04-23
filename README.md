# AutoLook

AutoLook 是一个本地视觉自动化实验项目。当前主流程已经收敛为：

1. 用 `pywin32` 找到游戏窗口，并截取客户区画面。
2. 用视觉模型识别目标宠物。
3. 根据目标框和画面中心的偏差，按方向键移动视角。
4. 目标进入中心容差范围后，点击捕捉键丢球。

项目默认 `dry_run: true`，不会发送真实输入；只有显式传入 `--live` 时才会控制键鼠。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev,control,yolo]
```

检查依赖和测试：

```powershell
python scripts/check_env.py
python -m pytest
```

## 快速运行

先 dry-run 验证识别和动作日志：

```powershell
python scripts/run_bot.py --dry-run --debug --max-runtime 10
```

确认无误后运行 live：

```powershell
python scripts/run_bot.py --live --debug --focus-click --start-delay 5 --max-runtime 10
```

如果希望运行时在游戏窗口上实时框选当前目标：

```powershell
python scripts/run_bot.py --live --debug --overlay-target --focus-click --start-delay 5 --max-runtime 100
```

常用参数：

```text
--live               启用真实键鼠输入
--dry-run            强制 dry-run
--debug              打印识别和动作日志
--overlay-target     在屏幕上实时框选当前目标
--overlay-color      目标框颜色，格式 #RRGGBB
--overlay-thickness  目标框线宽，单位像素
--focus-click        启动前激活游戏窗口并点击客户区中心
--start-delay        启动前等待秒数，方便切回游戏
--max-runtime        限制运行时长；调试 live 时建议先给小值
```

## 核心配置

默认配置在 `config/default.yaml`。

```yaml
window:
  title_keyword: "洛克王国"
  auto_locate: true
  use_client_area: true

app:
  overlay_target: false
  overlay_color: "#00FF00"
  overlay_thickness: 3

vision:
  backend: "yolo"
  model_path: "data/models/best.pt"
  yolo_confidence_threshold: 0.6

control:
  camera:
    center_tolerance_px: 15
    key_left: "left"
    key_right: "right"
    key_up: "up"
    key_down: "down"
  capture:
    ball_button: "left"
```

当前只有一个真实输入后端：`pydirectinput`。视角控制完全使用方向键；鼠标只用于最终丢球点击。

## 捕捉逻辑

当前捕捉顺序是：

```text
没有目标
-> 继续检测，释放方向键

发现目标但未居中
-> 根据目标相对中心的位置按方向键移动视角

目标进入中心容差范围
-> 释放方向键
-> mouse_down(ball_button)
-> mouse_up(ball_button)
```


## YOLO 检测

当前默认使用 YOLO 模型检测目标：

```yaml
vision:
  backend: "yolo"
  model_path: "data/models/best.pt"
  yolo_confidence_threshold: 0.6
```

YOLO 类别名需要和 `targets.pets[].detector_label` 一致：

```yaml
targets:
  pets:
    - name: "恶魔狼"
      enabled: true
      detector_label: "demon_wolf"
      min_confidence: 0.6
```

## 窗口定位

列出匹配窗口并查看截取区域：

```powershell
python scripts/list_windows.py --title 洛克王国
```

确认当前捕获区域：

```powershell
python scripts/calibrate_window.py
```

如果自动定位不稳定，可以临时关闭：

```yaml
window:
  auto_locate: false
  region:
    left: 0
    top: 0
    width: 2560
    height: 1440
```

## 对准调试

只检查识别和对准计算，不发送键鼠输入：

```powershell
python scripts/debug_aim.py --include-below-threshold
```

调试图会输出到：

```text
data/screenshots/aim_debug/
```

如果目标一直过不了中心判断，可以适当调大：

```yaml
control:
  camera:
    center_tolerance_px: 100
```

如果方向键反应太慢，可以缩短主循环间隔：

```yaml
app:
  tick_interval_seconds: 0.05
```

## 采集样本

批量采集截图：

```powershell
python scripts/collect_samples.py --count 200 --interval 0.5 --delay 3
```

采集时尽量覆盖不同地图、距离、光照和目标角度。
