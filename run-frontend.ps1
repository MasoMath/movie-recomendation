$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "frontend")
$env:NODE_OPTIONS = "--use-system-ca"
npm run dev
