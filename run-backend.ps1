$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "backend")
& (Join-Path $root "venv\Scripts\python.exe") -m flask --app server.py --debug run
