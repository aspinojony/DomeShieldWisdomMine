"""指挥官：拉起 5 个子进程 + 系统托盘 + 自动开浏览器。"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import List


SERVICES = [
    # (name, port, 友好名)
    ("business_api", 8002, "业务 API"),
    ("sensor_api", 8000, "监测 API"),
    ("ai_engine", 8001, "AI 风险引擎"),
    ("vision_engine", 8003, "视觉识别"),
    ("frontend", 5173, "前端大屏"),
]
FRONTEND_URL = "http://127.0.0.1:5173/"


def _data_dir() -> Path:
    return Path(os.environ.get("MINING_DATA_DIR", "."))


def _logs_dir() -> Path:
    p = _data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _wait_port(port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def _spawn_service(name: str) -> subprocess.Popen:
    """以 launcher.exe --service=NAME 形式起一个子进程，所有 stdout/stderr 写日志文件。"""
    log_file = _logs_dir() / f"{name}.log"
    fh = open(log_file, "a", encoding="utf-8", buffering=1)
    fh.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} starting {name} =====\n")

    cmd = [sys.executable, "--service", name]
    creationflags = 0
    if os.name == "nt":
        # CREATE_NO_WINDOW 防止子进程弹黑框
        creationflags = 0x08000000

    return subprocess.Popen(
        cmd,
        stdout=fh,
        stderr=subprocess.STDOUT,
        cwd=str(_data_dir()),
        env=os.environ.copy(),
        creationflags=creationflags,
    )


class Supervisor:
    def __init__(self) -> None:
        self.procs: List[subprocess.Popen] = []
        self._stop = threading.Event()

    def start_all(self) -> None:
        for name, _port, _label in SERVICES:
            self.procs.append(_spawn_service(name))
            # 错开一点，业务 API 先起完再起后面的，缓解共抢端口/文件锁
            time.sleep(0.5)

    def wait_ready(self) -> List[str]:
        """返回未就绪的服务名列表。"""
        failed: List[str] = []
        for name, port, _label in SERVICES:
            if not _wait_port(port, timeout=45):
                failed.append(name)
        return failed

    def stop_all(self) -> None:
        self._stop.set()
        for p in self.procs:
            try:
                p.terminate()
            except Exception:
                pass
        # 给点时间优雅退
        deadline = time.time() + 5
        for p in self.procs:
            remaining = max(0.1, deadline - time.time())
            try:
                p.wait(timeout=remaining)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass


def run_supervisor(open_browser: bool = True, show_tray: bool = True) -> int:
    sup = Supervisor()
    sup.start_all()

    def _post_ready() -> None:
        failed = sup.wait_ready()
        if failed:
            # 没全起来也别拦着，用户能从托盘看到错误日志
            sys.stderr.write(f"[warn] services not ready: {', '.join(failed)}\n")
        if open_browser:
            try:
                webbrowser.open(FRONTEND_URL)
            except Exception:
                pass

    threading.Thread(target=_post_ready, daemon=True).start()

    if show_tray:
        try:
            _run_tray(sup)
        except Exception as exc:  # 托盘失败时退化为「按 Ctrl+C 退出」
            sys.stderr.write(f"[warn] tray failed: {exc}\n")
            _run_blocking(sup)
    else:
        _run_blocking(sup)

    sup.stop_all()
    return 0


def _run_blocking(sup: Supervisor) -> None:
    try:
        while not sup._stop.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def _run_tray(sup: Supervisor) -> None:
    """pystray 托盘：右键菜单可打开浏览器、打开日志目录、退出。"""
    import pystray
    from PIL import Image, ImageDraw

    def _icon_image() -> "Image.Image":
        # 简单画一个 64×64 的盾牌图标，没有 .ico 资源也能跑
        img = Image.new("RGBA", (64, 64), (15, 23, 42, 0))
        d = ImageDraw.Draw(img)
        d.polygon(
            [(32, 4), (58, 14), (58, 36), (32, 60), (6, 36), (6, 14)],
            fill=(56, 189, 248, 255),
            outline=(15, 23, 42, 255),
        )
        d.text((22, 22), "DS", fill=(15, 23, 42, 255))
        return img

    def _on_open(icon, item):
        webbrowser.open(FRONTEND_URL)

    def _on_logs(icon, item):
        if os.name == "nt":
            os.startfile(_logs_dir())  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["open", str(_logs_dir())])

    def _on_quit(icon, item):
        sup._stop.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("打开大屏", _on_open, default=True),
        pystray.MenuItem("打开日志目录", _on_logs),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", _on_quit),
    )
    icon = pystray.Icon("DomeShield", _icon_image(), "穹盾智矿", menu)
    icon.run()
