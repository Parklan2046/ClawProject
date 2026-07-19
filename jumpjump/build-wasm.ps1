# Build the Rust core into a wasm-bindgen --target web module.
# Output: ../wasm/jumpjump_core.js + ../wasm/jumpjump_core_bg.wasm
$ErrorActionPreference = "Stop"
Set-Location -Path (Join-Path $PSScriptRoot "wasm-src")

if (-not (Get-Command wasm-pack -ErrorAction SilentlyContinue)) {
    Write-Host "[build-wasm] wasm-pack not found — installing via cargo..."
    cargo install wasm-pack
}

wasm-pack build --release --target web --out-name jumpjump_core --out-dir ../wasm
Write-Host "[build-wasm] done. Files in jumpjump/wasm/"
Write-Host "[build-wasm] index.html will auto-detect the .wasm on next load."
