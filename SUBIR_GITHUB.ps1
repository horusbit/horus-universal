# HORUS Universal - Subir a GitHub
$PROJECT = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "  Subiendo HORUS Universal a GitHub..." -ForegroundColor Cyan
Write-Host ""

Set-Location $PROJECT

# Inicializar git si no existe
if (-not (Test-Path ".git")) {
    git init
    git branch -M main
}

# Configurar remote
$remoteExists = git remote get-url origin 2>$null
if (-not $remoteExists) {
    git remote add origin https://github.com/horusbit/horus-universal.git
} else {
    git remote set-url origin https://github.com/horusbit/horus-universal.git
}

# Crear .gitignore limpio
@"
__pycache__/
*.pyc
*.pyo
.env
.venv/
venv/
*.egg-info/
node_modules/
.next/
.vercel/
*.log
.DS_Store
Thumbs.db
.vscode/
.idea/
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8 -Force

# Add y commit
git add -A
git status
git commit -m "Dia 2: agentes especializados, auto-routing, sidebar UI, memoria Redis, model fallback"

# Push
Write-Host ""
Write-Host "  Haciendo push a GitHub..." -ForegroundColor Yellow
git push -u origin main --force

Write-Host ""
Write-Host "  LISTO - Codigo subido a GitHub!" -ForegroundColor Green
Write-Host "  https://github.com/horusbit/horus-universal" -ForegroundColor White
Write-Host ""
pause
