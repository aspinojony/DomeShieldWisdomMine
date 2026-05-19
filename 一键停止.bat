@echo off
chcp 65001 >nul
echo.
echo ====== 关闭穹盾智矿 ======
echo.
powershell -ExecutionPolicy Bypass -NoProfile -Command "foreach ($p in 5173,8000,8001,8002,8003) { $c = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue; if ($c) { foreach ($x in $c) { Stop-Process -Id $x.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host ('  [stop] :' + $p + ' (PID ' + $x.OwningProcess + ')') -ForegroundColor Yellow } } else { Write-Host ('  [skip] :' + $p + ' 没在跑') -ForegroundColor DarkGray } }"
echo.
echo 已全部关闭。
echo.
pause
