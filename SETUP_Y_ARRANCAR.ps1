$ErrorActionPreference = "Continue"
$host.UI.RawUI.WindowTitle = "HORUS Universal - Setup"
$PROJECT = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) { Write-Host ""; Write-Host "  >> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  [ERROR] $msg" -ForegroundColor Red }

Clear-Host
Write-Host ""
Write-Host "  ==========================================" -ForegroundColor Magenta
Write-Host "    HORUS Universal - Setup Automatico     " -ForegroundColor Magenta
Write-Host "  ==========================================" -ForegroundColor Magenta

# 1. Verificar Python
Write-Step "Verificando Python..."
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3") { $pythonCmd = $cmd; Write-OK "$ver"; break }
    } catch {}
}
if (-not $pythonCmd) { Write-Fail "Instala Python desde https://python.org"; pause; exit 1 }

# 2. Verificar Node.js
Write-Step "Verificando Node.js..."
try { $nodeVer = node --version 2>&1; Write-OK "Node.js $nodeVer" }
catch { Write-Fail "Instala Node.js desde https://nodejs.org"; pause; exit 1 }

# 3. Actualizar pip y limpiar cache
Write-Step "Actualizando pip y limpiando cache..."
& $pythonCmd -m pip install --upgrade pip --quiet 2>&1 | Out-Null
& $pythonCmd -m pip cache purge 2>&1 | Out-Null
Write-OK "pip actualizado y cache limpio"

# 4. Instalar Backend
Write-Step "Instalando Backend Python (2-3 min primera vez)..."
Set-Location "$PROJECT\backend"
$result = & $pythonCmd -m pip install -r requirements.txt --prefer-binary --no-warn-script-location 2>&1
$failed = $result | Where-Object { $_ -match "^ERROR" }
if ($failed) {
    Write-Fail "Error al instalar. Intentando sin version fija..."
    # Segundo intento: instalar uno por uno los criticos
    & $pythonCmd -m pip install fastapi uvicorn python-dotenv pydantic pydantic-settings --prefer-binary --quiet 2>&1 | Out-Null
    & $pythonCmd -m pip install supabase upstash-redis sse-starlette tenacity python-multipart --prefer-binary --quiet 2>&1 | Out-Null
}
Write-OK "Backend: dependencias instaladas"

# 5. Instalar Frontend
Write-Step "Instalando Frontend Node.js..."
Set-Location "$PROJECT\frontend"
npm install --legacy-peer-deps 2>&1 | Where-Object { $_ -notmatch "npm warn" } | Out-Default
Write-OK "Frontend: dependencias instaladas"

# 6. Icono PWA placeholder
$pngBytes = [Convert]::FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
foreach ($icon in @("$PROJECT\frontend\public\icon-192.png","$PROJECT\frontend\public\icon-512.png")) {
    if (-not (Test-Path $icon)) { [System.IO.File]::WriteAllBytes($icon, $pngBytes) }
}
Write-OK "Iconos PWA creados"

# 7. Arrancar Backend
Write-Step "Arrancando Backend FastAPI (puerto 8000)..."
Set-Location "$PROJECT\backend"
$backendProcess = Start-Process -FilePath $pythonCmd `
    -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000 --reload" `
    -PassThru -WindowStyle Normal
Write-OK "Backend PID: $($backendProcess.Id)"

# Esperar backend
Write-Step "Esperando que el backend arranque..."
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { Write-OK "Backend listo: http://localhost:8000"; break }
    } catch {}
    if ($i -eq 14) { Write-Host "  [!] Backend tarda mas de lo normal, continuando..." -ForegroundColor Yellow }
}

# 8. Arrancar Frontend
Write-Step "Arrancando Frontend Next.js (puerto 3000)..."
Set-Location "$PROJECT\frontend"
$frontendProcess = Start-Process -FilePath "cmd" `
    -ArgumentList "/c npm run dev" -PassThru -WindowStyle Normal
Write-OK "Frontend PID: $($frontendProcess.Id)"

# Esperar frontend
Write-Step "Compilando Next.js (puede tardar hasta 40 segundos)..."
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 3
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { Write-OK "Frontend listo"; break }
    } catch {}
    Write-Host "  ... compilando ($([int](($i+1)*3))s)" -ForegroundColor Gray
}

# 9. Abrir Edge
Write-Step "Abriendo HORUS en Edge..."
Start-Process "msedge" "http://localhost:3000" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  ==========================================" -ForegroundColor Green
Write-Host "    HORUS UNIVERSAL EN LINEA              " -ForegroundColor Green
Write-Host "  ==========================================" -ForegroundColor Green
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  Presiona Enter para cerrar este launcher" -ForegroundColor Gray
Write-Host "  (Los servidores siguen corriendo en sus ventanas)" -ForegroundColor Gray
Write-Host ""
pause
