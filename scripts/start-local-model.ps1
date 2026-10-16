$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$runtimePath = Join-Path $repositoryRoot 'artifacts\local-model\runtime\ollama.exe'
if (-not (Test-Path -LiteralPath $runtimePath)) {
    throw 'Run python scripts/setup_local_model.py first.'
}
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MODELS = Join-Path $repositoryRoot 'artifacts\local-model\models'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_CONTEXT_LENGTH = '4096'
New-Item -ItemType Directory -Force -Path $env:OLLAMA_MODELS | Out-Null
& $runtimePath serve
