$PROJECT = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonCmd = $null
foreach ($cmd in @("python","python3","py")) {
    try { $ver = & $cmd --version 2>&1; if ($ver -match "Python 3") { $pythonCmd = $cmd; break } } catch {}
}

Write-Host ""
Write-Host "  Instalando supabase sin dependencias problematicas..." -ForegroundColor Cyan

# Instalar supabase y sus deps directas SIN pyiceberg
& $pythonCmd -m pip install supabase --no-deps --quiet 2>&1 | Out-Null
& $pythonCmd -m pip install gotrue postgrest realtime storage3 supafunc --prefer-binary --quiet 2>&1 | Out-Null

# Verificar
$test = & $pythonCmd -c "import supabase; print('OK')" 2>&1
if ($test -match "OK") {
    Write-Host "  [OK] supabase instalado correctamente" -ForegroundColor Green
} else {
    Write-Host "  [!] supabase no disponible - backend correra en modo dev (sin auth)" -ForegroundColor Yellow
}

# Matar backend anterior si existe
Get-Process | Where-Object { $_.Name -like "*uvicorn*" -or ($_.CommandLine -like "*uvicorn*") } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  Arrancando Backend..." -ForegroundColor Cyan
Set-Location "$PROJECT\backend"
Start-Process -FilePath $pythonCmd `
    -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" `
    -WindowStyle Normal

Write-Host "  [OK] Backend arrancando en http://localhost:8000" -ForegroundColor Green
Write-Host "  [OK] API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "  Abre http://localhost:3000 en Edge para usar HORUS" -ForegroundColor White
Write-Host ""
Start-Sleep -Seconds 3
Start-Process "msedge" "http://localhost:8000/docs"
pause
