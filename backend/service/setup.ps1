param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$serviceDirectory = $PSScriptRoot
& $Python -c "import sys; assert sys.version_info[:2] == (3, 12), 'Use Python 3.12 for the tested environment'"
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required.' }
if (-not (Test-Path -LiteralPath (Join-Path $serviceDirectory '.venv\Scripts\python.exe'))) {
    & $Python -m venv (Join-Path $serviceDirectory '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create service venv.' }
}
& (Join-Path $serviceDirectory '.venv\Scripts\python.exe') -m pip install -r (Join-Path $serviceDirectory 'requirements.lock.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
Write-Output 'Service environment ready. Run backend\service\start_api.cmd.'
