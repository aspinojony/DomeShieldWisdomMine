"""穹盾智矿 Windows 启动器入口。

两种运行模式：
- 默认：作为「指挥官」拉起所有服务、托盘、自动开浏览器
- --service NAME：作为「工人」执行单个服务（由指挥官 spawn 自己实现）

PyInstaller 打包后，sys.executable 就是 launcher.exe 自身；
子进程通过再次执行自己 + 不同的 argv 实现「一个 exe 跑多个服务」。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _resolve_app_root() -> Path:
    """返回应用资源根目录（包含 backend_service/ai_core/web 三个子目录）。"""
    # PyInstaller 冻结模式下，资源被解压到 sys._MEIPASS
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    # 开发模式下：windows-installer/launcher/__main__.py，上溯两层
    return Path(__file__).resolve().parents[2]


def _ensure_data_dir() -> Path:
    """%APPDATA%\\穹盾智矿，不存在则创建。开发模式回落到项目内 data/。"""
    appdata = os.environ.get("APPDATA")
    if appdata:
        data = Path(appdata) / "穹盾智矿"
    else:
        data = _resolve_app_root() / "data"
    (data / "logs").mkdir(parents=True, exist_ok=True)
    return data


def _bootstrap_env() -> None:
    """把 sys.path、PYTHONPATH、数据目录等环境变量准备好。"""
    app_root = _resolve_app_root()
    data_dir = _ensure_data_dir()

    # 让 import database / import settings / from models.cv... 能找得到
    for sub in ("backend_service", "ai_core"):
        p = str(app_root / sub)
        if p not in sys.path:
            sys.path.insert(0, p)

    # 这些环境变量会被各服务读到
    os.environ.setdefault("MINING_DATA_DIR", str(data_dir))
    os.environ.setdefault(
        "DATABASE_URL", f"sqlite:///{(data_dir / 'mining.db').as_posix()}"
    )
    os.environ.setdefault("DEMO_MODE", "true")

    # 视觉服务需要 ai_core 作为 cwd 才能 import models.cv.*
    os.environ["MINING_APP_ROOT"] = str(app_root)


def _run_service(name: str) -> int:
    """工人模式：在当前进程里 import 并运行某个服务。"""
    import uvicorn

    if name == "business_api":
        os.chdir(_resolve_app_root() / "backend_service")
        from business_api import app  # type: ignore
        uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")
    elif name == "sensor_api":
        os.chdir(_resolve_app_root() / "backend_service")
        from api_server import app  # type: ignore
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
    elif name == "ai_engine":
        os.chdir(_resolve_app_root() / "backend_service")
        from ai_prediction_engine import app  # type: ignore
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
    elif name == "vision_engine":
        os.chdir(_resolve_app_root() / "ai_core")
        from vision_inference_service import app  # type: ignore
        uvicorn.run(app, host="127.0.0.1", port=8003, log_level="warning")
    elif name == "frontend":
        from launcher.static_server import serve  # type: ignore
        serve(_resolve_app_root() / "web", port=5173)
    else:
        print(f"unknown service: {name}", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="穹盾智矿")
    parser.add_argument("--service", help="以子进程身份运行单个服务", default=None)
    parser.add_argument(
        "--no-browser", action="store_true", help="启动后不自动打开浏览器"
    )
    parser.add_argument(
        "--no-tray", action="store_true", help="不显示托盘（仅供调试）"
    )
    args = parser.parse_args()

    _bootstrap_env()

    if args.service:
        return _run_service(args.service)

    # 指挥官模式
    from launcher.tray import run_supervisor  # type: ignore
    return run_supervisor(open_browser=not args.no_browser, show_tray=not args.no_tray)


if __name__ == "__main__":
    sys.exit(main())
