# 穹盾智矿 Windows 安装包构建脚本
# 用法（项目根目录下）：
#   powershell -ExecutionPolicy Bypass -File windows-installer\build.ps1
#
# 前提：Python 3.11、Node.js 20、Inno Setup 6 已安装并加入 PATH。
# 输出：windows-installer\output\穹盾智矿-Setup-<version>.exe

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8

$root = (Resolve-Path "$PSScriptRoot\..").Path
$installerDir = "$root\windows-installer"
$outDir = "$installerDir\output"
$buildVenv = "$installerDir\.build-venv"

$version = "1.0.0"
Write-Host "==== 穹盾智矿 v$version 打包流程 ====" -ForegroundColor Cyan
Write-Host "项目根: $root"

# ---- 0. 占位图标 ----
$iconPath = "$installerDir\assets\icon.ico"
if (-not (Test-Path $iconPath)) {
    Write-Host "`n[0/5] 生成占位图标 icon.ico..." -ForegroundColor Yellow
    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap(64, 64)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear([System.Drawing.Color]::FromArgb(0, 15, 23, 42))
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 56, 189, 248))
    $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255, 15, 23, 42), 2)
    $points = @(
        (New-Object System.Drawing.PointF(32, 4)),
        (New-Object System.Drawing.PointF(58, 14)),
        (New-Object System.Drawing.PointF(58, 36)),
        (New-Object System.Drawing.PointF(32, 60)),
        (New-Object System.Drawing.PointF(6, 36)),
        (New-Object System.Drawing.PointF(6, 14))
    )
    $g.FillPolygon($brush, $points)
    $g.DrawPolygon($pen, $points)
    $g.Dispose()
    $icon = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())
    $fs = [System.IO.File]::Create($iconPath)
    $icon.Save($fs)
    $fs.Close()
    $bmp.Dispose()
}

# ---- 1. 前端构建 ----
Write-Host "`n[1/5] 构建前端..." -ForegroundColor Yellow
Push-Location "$root\frontend_dashboard"
if (-not (Test-Path node_modules)) {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install 失败" }
}
npm run build
if ($LASTEXITCODE -ne 0) { throw "npm run build 失败" }
Pop-Location
if (-not (Test-Path "$root\frontend_dashboard\dist\index.html")) {
    throw "前端构建产物缺失：frontend_dashboard\dist\index.html"
}

# ---- 2. 准备打包专用 venv ----
Write-Host "`n[2/5] 准备打包 venv..." -ForegroundColor Yellow
if (-not (Test-Path $buildVenv)) {
    python -m venv $buildVenv
    if ($LASTEXITCODE -ne 0) { throw "venv 创建失败" }
}
$pip = "$buildVenv\Scripts\pip.exe"
$py  = "$buildVenv\Scripts\python.exe"

& $py -m pip install --upgrade pip
# 业务依赖
& $pip install `
    fastapi "uvicorn[standard]" sqlalchemy pydantic `
    "python-jose[cryptography]" "passlib[bcrypt]" python-multipart `
    influxdb-client pandas numpy scikit-learn requests pyyaml `
    matplotlib tqdm opencv-python
if ($LASTEXITCODE -ne 0) { throw "业务依赖安装失败" }

# AI 依赖（CPU 版 torch）
& $pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw "torch 安装失败" }
& $pip install ultralytics
if ($LASTEXITCODE -ne 0) { throw "ultralytics 安装失败" }

# 启动器依赖
& $pip install -r "$installerDir\requirements-launcher.txt"
if ($LASTEXITCODE -ne 0) { throw "启动器依赖安装失败" }

# ---- 3. PyInstaller 打包 ----
Write-Host "`n[3/5] PyInstaller 打包 launcher..." -ForegroundColor Yellow
$pyiBuild = "$installerDir\build"
$pyiDist  = "$installerDir\dist"
Remove-Item -Recurse -Force $pyiBuild -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $pyiDist  -ErrorAction SilentlyContinue

Push-Location $installerDir
& $py -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath "$pyiDist" `
    --workpath "$pyiBuild" `
    launcher.spec
$rc = $LASTEXITCODE
Pop-Location
if ($rc -ne 0) { throw "PyInstaller 失败" }

if (-not (Test-Path "$pyiDist\DomeShield\穹盾智矿.exe")) {
    throw "未生成 DomeShield\穹盾智矿.exe，请查看 PyInstaller 日志"
}

# ---- 4. Inno Setup 编译 ----
Write-Host "`n[4/5] Inno Setup 编译安装包..." -ForegroundColor Yellow
$iscc = $null
foreach ($cand in @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)) {
    if (Test-Path $cand) { $iscc = $cand; break }
}
if (-not $iscc) {
    Write-Warning "未找到 Inno Setup 6，跳过最终封装。"
    Write-Warning "可手动运行：ISCC.exe `"$installerDir\installer.iss`""
} else {
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    & $iscc /Q "/DAPP_VERSION=$version" "$installerDir\installer.iss"
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup 编译失败" }
}

# ---- 5. 收尾 ----
Write-Host "`n[5/5] 完成" -ForegroundColor Green
if (Test-Path $outDir) {
    Get-ChildItem $outDir -Filter "*.exe" | ForEach-Object {
        Write-Host "  -> $($_.FullName)" -ForegroundColor Green
    }
}
Write-Host "原始 onedir 目录: $pyiDist\DomeShield" -ForegroundColor DarkGray
