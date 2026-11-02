# Starts llama-server with Jebadiah 9B v2.1 (Q4_K_M) on CPU.
# Matches the model card's tested setup: 4096 context, 1 slot. Binds to localhost only.
param(
    [int]$Port = 8080,
    [int]$Threads = 4   # i7-1165G7 has 4 physical cores
)

$root  = $PSScriptRoot
$exe   = Join-Path $root 'tools\llama.cpp\llama-server.exe'
$model = Join-Path $root 'models\jeb-9b-v2.1\jebadiah-9b-v2-1-Q4_K_M.gguf'

& $exe -m $model `
    --host 127.0.0.1 --port $Port `
    -ngl 0 -t $Threads `
    -c 4096 -np 1
