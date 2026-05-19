# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec：把整个 launcher + 后端源码 + 前端 dist 打成一个 onedir 应用。

构建期约定：
- ROOT 就是仓库根目录
- 前端必须已经 npm run build 过（dist/ 存在）
- backend_service / ai_core 的所有 .py 会作为 data 文件随包一起带走
"""
from pathlib import Path
import sys

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    collect_dynamic_libs,
)

ROOT = Path(SPECPATH).resolve().parent  # SPECPATH = windows-installer/
LAUNCHER = ROOT / "windows-installer" / "launcher"

datas = []
binaries = []

# ---- 后端 / AI 源码（运行时 import）----
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

# ---- 三方依赖：用 collect_* 强制把整个包打进去 ----
# launcher/__main__.py 没有静态 import fastapi 等，PyInstaller 自动扫不到。
# 这里显式告诉它要带哪些包。
_packages_full = [
    # Web 框架
    "fastapi",
    "pydantic",
    "pydantic_core",
    "starlette",
    "uvicorn",
    "anyio",
    "sniffio",
    "h11",
    "httptools",
    "websockets",
    "watchfiles",
    "click",
    "typing_extensions",
    # 认证
    "jose",
    "passlib",
    "bcrypt",
    "cryptography",
    # ORM
    "sqlalchemy",
    # 数据
    "numpy",
    "pandas",
    "sklearn",
    "scipy",
    "yaml",
    "requests",
    "urllib3",
    "certifi",
    "charset_normalizer",
    "idna",
    "influxdb_client",
    "dateutil",
    "pytz",
    # AI
    "ultralytics",
    "cv2",
    # 启动器
    "pystray",
    "PIL",
]

hidden = []
for pkg in _packages_full:
    try:
        hidden += collect_submodules(pkg)
    except Exception as exc:
        sys.stderr.write(f"[spec] collect_submodules({pkg}) failed: {exc}\n")
    try:
        datas += collect_data_files(pkg)
    except Exception as exc:
        sys.stderr.write(f"[spec] collect_data_files({pkg}) failed: {exc}\n")

# DLL / so 这些跟着 torch、cv2、numpy 走
for pkg in ("torch", "torchvision", "cv2", "numpy", "scipy", "sklearn", "pandas"):
    try:
        binaries += collect_dynamic_libs(pkg)
    except Exception as exc:
        sys.stderr.write(f"[spec] collect_dynamic_libs({pkg}) failed: {exc}\n")

# torch / torchvision 单独 collect（包太大，submodules 用 filter 可能漏）
for pkg in ("torch", "torchvision"):
    try:
        hidden += collect_submodules(pkg)
    except Exception:
        pass
    try:
        datas += collect_data_files(pkg, include_py_files=False)
    except Exception:
        pass

# 本地业务模块
hidden += [
    "business_api",
    "api_server",
    "ai_prediction_engine",
    "vision_inference_service",
    "database",
    "auth",
    "models",
    "settings",
    "data_ingestion",
]

# 去重
hidden = sorted(set(hidden))

a = Analysis(
    [str(LAUNCHER / "__main__.py")],
    pathex=[
        str(ROOT),
        str(LAUNCHER.parent),
        str(ROOT / "backend_service"),
        str(ROOT / "ai_core"),
    ],
    binaries=binaries,
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
