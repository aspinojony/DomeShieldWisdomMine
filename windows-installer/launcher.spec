# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec：把整个 launcher + 后端源码 + 前端 dist 打成一个 onedir 应用。

构建期约定：
- ROOT 就是仓库根目录
- 前端必须已经 npm run build 过（dist/ 存在）
- backend_service / ai_core 的所有 .py 会作为 data 文件随包一起带走
"""
from pathlib import Path
import sys

ROOT = Path(SPECPATH).resolve().parent  # SPECPATH = windows-installer/
LAUNCHER = ROOT / "windows-installer" / "launcher"

datas = []

# 后端 / AI 源码（运行时 import）
def _collect_py(src_dir: Path, dest: str):
    out = []
    for p in src_dir.rglob("*"):
        if p.is_dir():
            continue
        if "__pycache__" in p.parts:
            continue
        if p.suffix in {".pyc", ".pyo", ".log"}:
            continue
        rel = p.relative_to(src_dir).parent
        out.append((str(p), str(Path(dest) / rel)))
    return out

datas += _collect_py(ROOT / "backend_service", "backend_service")
datas += _collect_py(ROOT / "ai_core", "ai_core")

# 前端构建产物
frontend_dist = ROOT / "frontend_dashboard" / "dist"
if frontend_dist.exists():
    datas += _collect_py(frontend_dist, "web")
else:
    sys.stderr.write(
        "[spec] WARNING: frontend_dashboard/dist 不存在，请先 npm run build\n"
    )

# YOLO 权重
weights = ROOT / "ai_core" / "checkpoints" / "crack_yolo_best.pt"
if weights.exists():
    datas.append((str(weights), "ai_core/checkpoints"))

hidden = [
    "uvicorn.logging",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "passlib.handlers.bcrypt",
    "sqlalchemy.dialects.sqlite",
    "ultralytics",
    "cv2",
    "torch",
    "torchvision",
]

a = Analysis(
    [str(LAUNCHER / "__main__.py")],
    pathex=[str(ROOT), str(LAUNCHER.parent)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib.tests", "torch.test"],
    noarchive=False,
)
pyz = PYZ(a.pure)

icon_path = ROOT / "windows-installer" / "assets" / "icon.ico"

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="穹盾智矿",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # --windowed
    icon=str(icon_path) if icon_path.exists() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="DomeShield",
)
