# PowerShell setup script for Windows

$VenvPath = Join-Path $PSScriptRoot ".venv"
$EnvFile = Join-Path $PSScriptRoot ".env"
$ExampleEnvFile = Join-Path $PSScriptRoot ".env.example"

Write-Host "Setting up Python virtual environment..." -ForegroundColor Cyan

if (-not (Test-Path $VenvPath)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create python virtual environment. Make sure python is in your path."
        exit $LASTEXITCODE
    }
}

# Run commands in the venv context
$PipPath = Join-Path $VenvPath "Scripts\pip.exe"

Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $PipPath install --upgrade pip

Write-Host "Installing requirements..." -ForegroundColor Cyan
& $PipPath install -r requirements.txt

if (-not (Test-Path $EnvFile)) {
    Copy-Item $ExampleEnvFile $EnvFile
    Write-Host "Created .env from .env.example. Please fill in your real credentials in .env before running." -ForegroundColor Yellow
} else {
    Write-Host ".env already exists." -ForegroundColor Green
}

Write-Host "`nSetup complete! To run the bot locally in polling mode, execute:" -ForegroundColor Green
Write-Host "powershell -ExecutionPolicy Bypass -Command `".\.venv\Scripts\Activate.ps1; python -m src.main`"" -ForegroundColor Cyan
