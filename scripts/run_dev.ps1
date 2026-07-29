$ErrorActionPreference = 'Stop'

if (Test-Path .venv/Scripts/Activate.ps1) {
    . .venv/Scripts/Activate.ps1
}

Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000" -PassThru | Out-Null
Start-Process -FilePath "npm" -ArgumentList "--prefix", "frontend", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173" -PassThru | Out-Null

Write-Host "Backend and frontend processes started."
