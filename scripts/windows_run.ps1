# 穹盾智矿 Windows 一键启动脚本
# 双击 一键启动.bat 会调用本脚本，自动装依赖、起 5 个服务、开浏览器

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $root

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "         穹盾智矿  一键启动" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ---------- 0. 检查 Python ----------
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "[X] 没装 Python！" -ForegroundColor Red
    Write-Host ""
    Write-Host "    请先去下面这个网址下载 Python 3.11：" -ForegroundColor Yellow
    Write-Host "    https://www.python.org/downloads/release/python-3119/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    安装时务必勾选『Add Python to PATH』那一项！" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "    按回车退出"
    exit 1
}
$pyver = (& python --version) 2>&1
Write-Host "[OK] Python 已装：$pyver" -ForegroundColor Green

# ---------- 1. 检查 Node ----------
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "[X] 没装 Node.js！" -ForegroundColor Red
    Write-Host ""
    Write-Host "    请先去下面这个网址下载 Node.js 20 LTS：" -ForegroundColor Yellow
    Write-Host "    https://nodejs.org/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "    按回车退出"
    exit 1
}
$nodever = (& node --version) 2>&1
Write-Host "[OK] Node.js 已装：$nodever" -ForegroundColor Green

Write-Host ""

# ---------- 2. 业务后端 venv ----------
if (-not (Test-Path "backend_service\venv\Scripts\python.exe")) {
    Write-Host "[1/4] 第一次运行：建后端 venv + 装依赖（约 3-5 分钟）..." -ForegroundColor Yellow
    python -m venv backend_service\venv
    & backend_service\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
    & backend_service\venv\Scripts\pip.exe install --quiet `
        fastapi "uvicorn[standard]" sqlalchemy pydantic `
        "python-jose[cryptography]" "passlib[bcrypt]" python-multipart `
        influxdb-client pandas numpy scikit-learn requests pyyaml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] 后端依赖装失败" -ForegroundColor Red
        Read-Host "按回车退出"; exit 1
    }
    Write-Host "[OK] 后端依赖装好了" -ForegroundColor Green
} else {
    Write-Host "[1/4] 后端 venv 已存在，跳过" -ForegroundColor DarkGray
}

# ---------- 3. AI / 视觉 venv ----------
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host ""
    Write-Host "[2/4] 第一次运行：建 AI venv + 装 PyTorch（约 10-20 分钟，请耐心）..." -ForegroundColor Yellow
    python -m venv venv
    & venv\Scripts\python.exe -m pip install --upgrade pip --quiet
    Write-Host "      正在下载 PyTorch（CPU 版，约 200MB）..." -ForegroundColor DarkGray
    & venv\Scripts\pip.exe install --quiet torch torchvision --index-url https://download.pytorch.org/whl/cpu
    Write-Host "      正在装其它 AI 依赖..." -ForegroundColor DarkGray
    & venv\Scripts\pip.exe install --quiet `
        ultralytics opencv-python pyyaml numpy pandas scikit-learn `
        fastapi "uvicorn[standard]" pydantic requests matplotlib tqdm
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] AI 依赖装失败" -ForegroundColor Red
        Read-Host "按回车退出"; exit 1
    }
    Write-Host "[OK] AI 依赖装好了" -ForegroundColor Green
} else {
    Write-Host "[2/4] AI venv 已存在，跳过" -ForegroundColor DarkGray
}

# ---------- 4. 前端依赖 ----------
if (-not (Test-Path "frontend_dashboard\node_modules")) {
    Write-Host ""
    Write-Host "[3/4] 第一次运行：装前端依赖（约 2-5 分钟）..." -ForegroundColor Yellow
    Push-Location frontend_dashboard
    npm install --silent
    $rc = $LASTEXITCODE
    Pop-Location
    if ($rc -ne 0) {
        Write-Host "[X] 前端依赖装失败" -ForegroundColor Red
        Read-Host "按回车退出"; exit 1
    }
    Write-Host "[OK] 前端依赖装好了" -ForegroundColor Green
} else {
    Write-Host "[3/4] 前端依赖已存在，跳过" -ForegroundColor DarkGray
}

# ---------- 5. 启动 5 个服务 ----------
Write-Host ""
Write-Host "[4/4] 启动 5 个后台服务..." -ForegroundColor Yellow

$logDir = "$env:TEMP\tiankong-system"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Start-Svc($name, $port, $workdir, $cmd) {
    $busy = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($busy) {
        Write-Host "  [SKIP]  $name :$port 已被占用（可能上次没退干净）" -ForegroundColor DarkYellow
        return
    }
    Write-Host "  [START] $name -> :$port"
    Start-Process -WindowStyle Hidden -WorkingDirectory $workdir -FilePath "powershell" `
        -ArgumentList "-NoProfile","-Command",$cmd `
        -RedirectStandardOutput "$logDir\$name.log" `
        -RedirectStandardError  "$logDir\$name.err.log"
    Start-Sleep -Milliseconds 800
}

Start-Svc business_api 8002 "$root\backend_service" `
    "& '$root\backend_service\venv\Scripts\uvicorn.exe' business_api:app --host 127.0.0.1 --port 8002"

Start-Svc sensor_api 8000 $root `
    "`$env:DEMO_MODE='true'; & '$root\backend_service\venv\Scripts\python.exe' backend_service\api_server.py"

Start-Svc ai_engine 8001 $root `
    "& '$root\venv\Scripts\python.exe' backend_service\ai_prediction_engine.py"

Start-Svc vision_api 8003 $root `
    "& '$root\venv\Scripts\python.exe' ai_core\vision_inference_service.py"

Start-Svc frontend 5173 "$root\frontend_dashboard" `
    "npm run dev -- --host 127.0.0.1"

Write-Host ""
Write-Host "等 15 秒让服务全部起来..." -ForegroundColor Cyan
Start-Sleep -Seconds 15

Start-Process "http://127.0.0.1:5173"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "          启动完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  浏览器已自动打开：http://127.0.0.1:5173"
Write-Host "  登录账号：admin"
Write-Host "  登录密码：admin123"
Write-Host ""
Write-Host "  关闭项目：双击   一键停止.bat"
Write-Host "  日志目录：$logDir"
Write-Host ""
Write-Host "  这个黑窗关掉不会关项目，项目在后台跑。"
Write-Host ""
Read-Host "  按回车关掉这个窗口"
