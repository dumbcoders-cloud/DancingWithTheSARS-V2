$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python).Source }

& $pythonExe -m pip install -r requirements-desktop.txt
if ($LASTEXITCODE -ne 0) { throw "Installing desktop dependencies failed." }

& $pythonExe scripts/create_icon.py
if ($LASTEXITCODE -ne 0) { throw "Generating the application icon failed." }

& $pythonExe -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name DancingWithTheSARs `
  --icon "assets/dancing_with_the_sars.ico" `
  --collect-all fastapi `
  --collect-all flask `
  --collect-all a2wsgi `
  --collect-all uvicorn `
  --collect-all pydeck `
  --add-data "src;src" `
  --add-data "assets;assets" `
  scripts/launch_desktop.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "Windows executable: dist/DancingWithTheSARs.exe"
