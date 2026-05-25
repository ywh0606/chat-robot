# 终止占用8001端口的进程
$processes = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
if ($processes) {
    foreach ($proc in $processes) {
        Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "已终止进程: $($proc.OwningProcess)"
    }
    Start-Sleep -Seconds 2
}

# 启动新服务
Set-Location "e:\my_java_idea_file\chat-robot\backend"
Start-Process python -ArgumentList "start_new.py" -NoNewWindow
Write-Host "服务已启动在 http://localhost:8001"
