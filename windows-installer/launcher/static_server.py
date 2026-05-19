"""SPA 静态前端服务器：支持 history 模式（找不到文件回退 index.html）。"""
from __future__ import annotations

import http.server
import os
import socketserver
import sys
from pathlib import Path


class SPARequestHandler(http.server.SimpleHTTPRequestHandler):
    """SPA-friendly：对不存在的路径返回 index.html。"""

    def do_GET(self):  # noqa: N802
        # 把 URL 路径转成磁盘路径
        path = self.translate_path(self.path.split("?", 1)[0])
        if not os.path.exists(path) and not self.path.startswith("/assets"):
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, fmt, *args):  # 不污染日志
        pass


def serve(web_root: Path, port: int = 5173) -> None:
    if not web_root.exists():
        sys.stderr.write(f"[frontend] web root missing: {web_root}\n")
        sys.exit(1)

    os.chdir(str(web_root))

    handler = SPARequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        httpd.serve_forever()
