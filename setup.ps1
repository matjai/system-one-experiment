# One-time setup on a fresh clone: Python env, llama.cpp (CPU build) and the Jebadiah 9B v2.1 Q4_K_M model.
# Needs uv (https://docs.astral.sh/uv/). Downloads about 5.8 GB.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

$LlamaBuild = 'b12032'
$Repo       = 'frontier-infra/jebadiah-9b-v2-1-GGUF'
$Gguf       = 'jebadiah-9b-v2-1-Q4_K_M.gguf'
$GgufSha256 = 'cb29828caeba5d379e61e7606a988fcc13c4b6f6c77610155dcea1ed7a968e2b'
$ModelDir   = 'models\jeb-9b-v2.1'
$py         = '.venv\Scripts\python.exe'

Write-Host '== Python environment'
if (-not (Test-Path $py)) { uv venv .venv --python 3.12 }
uv pip install --python $py -r requirements.txt

Write-Host "== llama.cpp $LlamaBuild (CPU)"
if (-not (Test-Path 'tools\llama.cpp\llama-server.exe')) {
    New-Item -ItemType Directory -Force 'tools\llama.cpp' | Out-Null
    $zip = "tools\llama-$LlamaBuild-bin-win-cpu-x64.zip"
    Invoke-WebRequest "https://github.com/ggml-org/llama.cpp/releases/download/$LlamaBuild/llama-$LlamaBuild-bin-win-cpu-x64.zip" -OutFile $zip
    Expand-Archive $zip -DestinationPath 'tools\llama.cpp' -Force
    Remove-Item $zip
}

Write-Host "== Model files from $Repo"
& $py -c "from huggingface_hub import snapshot_download; snapshot_download('$Repo', allow_patterns=['scripts/*','*.json','*.jinja','*.txt','*.md','$Gguf'], local_dir=r'$ModelDir')"

Write-Host '== Verifying checksum'
$hash = (Get-FileHash (Join-Path $ModelDir $Gguf) -Algorithm SHA256).Hash.ToLower()
if ($hash -ne $GgufSha256) { throw "Checksum mismatch for $Gguf ($hash)" }
Write-Host 'Setup complete. Start the engine with .\start-server.ps1, then run .venv\Scripts\python.exe app.py'
