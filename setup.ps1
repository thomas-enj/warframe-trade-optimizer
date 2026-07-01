Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "====== [1/4] Venv already exists ======" -ForegroundColor Cyan
} else {
    Write-Host "====== [1/4] Creating venv ======" -ForegroundColor Cyan
    if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv venv }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { python -m venv venv }
    else {
        Write-Host "ERROR: Python 3 is not installed." -ForegroundColor Red
        Exit 1
    }
}

# On utilise directement les exécutables du venv pour être sûr de ne pas polluer le Python global
Write-Host "`n====== [2/4] Checking/Installing requirements ======" -ForegroundColor Cyan
if (Test-Path ".\requirements.txt") {
    .\venv\Scripts\pip.exe install -r requirements.txt
}

Write-Host "`n====== [3/4] Playwright (Chromium) configuration ======" -ForegroundColor Cyan
.\venv\Scripts\playwright.exe install chromium

Write-Host "`n====== [4/4] Configuration completed ! ======" -ForegroundColor Green
Write-Host "To start developing, activate your venv with:" -ForegroundColor Yellow
Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor Magenta