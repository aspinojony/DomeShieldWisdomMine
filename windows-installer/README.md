# 穹盾智矿 · Windows 安装包构建指南

把整个矿山系统打成一个 **双击安装、桌面有图标、自动开机可选** 的标准 Windows 应用。
产出：`windows-installer/output/穹盾智矿-Setup-1.0.0.exe`（约 1.5-2GB）。

---

## 1. 这是怎么工作的

1. 前端 `npm run build` → `frontend_dashboard/dist/`
2. 一个 PyInstaller 启动器 `穹盾智矿.exe`：
   - 双击后**指挥官模式**：spawn 5 个子进程 + 系统托盘 + 自动开浏览器
   - 子进程是它自己以 `--service NAME` 形式再启动一次（**一个 exe 跑 5 个服务**）
3. 写数据落在 `%APPDATA%\穹盾智矿\`（SQLite、日志、视觉历史），避开 Program Files 只读限制
4. Inno Setup 把 PyInstaller 的 onedir 产物 + 卸载器封成单一 .exe 安装包

服务端口跟开发环境完全一致：

| 服务 | 端口 |
|---|---|
| 前端大屏 | 5173 |
| 监测 API | 8000 |
| AI 引擎 | 8001 |
| 业务 API | 8002 |
| 视觉识别 | 8003 |

---

## 2. 构建机环境准备（**只在 Windows 上跑**）

| 工具 | 版本 | 下载 |
|---|---|---|
| Python | 3.11.x（**不要 3.13+**，torch 还没轮子） | https://www.python.org/downloads/ |
| Node.js | 20 LTS | https://nodejs.org/ |
| Inno Setup | 6.x | https://jrsoftware.org/isdl.php |

装完都要在 PowerShell 里能找到：
```powershell
python --version    # Python 3.11.x
node --version      # v20.x
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /?
```

另外需要一个图标文件，看 `assets/README.md`，把任意 `.ico` 放成 `assets/icon.ico` 即可。

---

## 3. 一键构建

在仓库根目录下：

```powershell
powershell -ExecutionPolicy Bypass -File windows-installer\build.ps1
```

流程：
1. `npm install` + `npm run build`
2. 创建打包专用 venv，装 fastapi/torch/ultralytics/pystray/pyinstaller
3. PyInstaller 按 `launcher.spec` 打包成 `windows-installer\dist\DomeShield\`
4. Inno Setup 把 onedir 封成 `output\穹盾智矿-Setup-1.0.0.exe`

**首次跑约 30-60 分钟**（torch CPU 版下载 ~200MB，打包阶段 LZMA 压缩 ~3GB onedir 很慢）。
第二次跑会复用 venv，**通常 5-10 分钟**。

---

## 4. 手动分步（出错时排查）

### 4.1 只构建前端
```powershell
cd frontend_dashboard
npm install
npm run build
```

### 4.2 只跑 PyInstaller
```powershell
cd windows-installer
.\.build-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean launcher.spec
```
输出在 `windows-installer\dist\DomeShield\`，可直接双击 `穹盾智矿.exe` 测试。

### 4.3 只跑 Inno Setup
```powershell
cd windows-installer
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

---

## 5. 调试 launcher（不打包，直接 Python 跑）

```powershell
cd C:\path\to\项目根
$env:PYTHONPATH = (Get-Location).Path
.\windows-installer\.build-venv\Scripts\python.exe -m windows-installer.launcher
```

或单独跑某个服务看错误：
```powershell
.\windows-installer\.build-venv\Scripts\python.exe -m windows-installer.launcher --service business_api
```

服务日志在 `%APPDATA%\穹盾智矿\logs\*.log`。

---

## 6. 用户侧体验

装完之后：

1. 开始菜单 / 桌面有 **穹盾智矿** 图标，双击启动
2. 任务栏右下角出现盾牌托盘图标
3. 默认浏览器自动打开 `http://127.0.0.1:5173`
4. 登录 `admin / admin123`
5. 关闭：托盘右键 → 退出（会停掉 5 个后端进程）
6. 卸载：开始菜单 → 卸载 穹盾智矿

数据保留在 `%APPDATA%\穹盾智矿\`，卸载不会删——想干净卸载手动删除该目录。

---

## 7. 常见问题

**Q: `穹盾智矿.exe` 双击没反应**
看 `%APPDATA%\穹盾智矿\logs\` 下日志。最可能是某个 hidden import 没打进来，给 `launcher.spec` 的 `hidden` 列表追加。

**Q: ultralytics / cv2 加载失败**
`launcher.spec` 已声明 hidden import，但有时 PyInstaller hook 不全。尝试：
```powershell
& $py -m pip install --upgrade pyinstaller pyinstaller-hooks-contrib
```

**Q: 安装包太大（>2GB）**
torch 是大头（~800MB）。可选：
- 把 YOLO 推理改成 ONNX Runtime，去掉 torch（工作量大）
- 用 UPX 压缩 dll：`launcher.spec` 中 `upx=True` 并安装 UPX

**Q: 中文路径导致打包失败**
当前项目根含中文（`天空一体矿山系统`），PyInstaller 多数情况能扛，但偶尔会报 UnicodeError。
解决：把仓库 clone 到纯英文路径如 `C:\projects\domeshield` 再构建。

**Q: Inno Setup 报 "Compiler error: cannot open ChineseSimplified.isl"**
Inno Setup 6 自带简中语言文件，但旧版本可能缺失。从 https://jrsoftware.org/files/istrans/ 下载 `ChineseSimplified.isl` 放到 Inno Setup 安装目录的 `Languages\` 下。

**Q: 防火墙弹窗**
首次启动时 Windows Defender 会问要不要允许 Python 监听端口，**勾"专用网络"** 即可。
生产部署建议给安装包做代码签名，避免 SmartScreen 拦截。

---

## 8. 文件清单

```
windows-installer/
├── README.md                  ← 本文件
├── build.ps1                  ← 一键打包脚本
├── installer.iss              ← Inno Setup 配置
├── launcher.spec              ← PyInstaller 配置
├── requirements-launcher.txt  ← 启动器额外依赖
├── assets/
│   ├── README.md              ← 图标说明
│   └── icon.ico               ← (需自行放置)
└── launcher/
    ├── __init__.py
    ├── __main__.py            ← 入口（指挥官/工人分发）
    ├── tray.py                ← 系统托盘 + 子进程管理
    └── static_server.py       ← 前端 dist 静态服务器
```
