#!/usr/bin/env bash
# Build the Rust core into a wasm-bindgen `--target web` module.
# Output goes into ../wasm/ as jumpjump_core.js + jumpjump_core_bg.wasm.
# Requires: rustup + `rustup target add wasm32-unknown-unknown` + wasm-pack.
set -euo pipefail

cd "$(dirname "$0")/wasm-src"

if ! command -v wasm-pack >/dev/null 2>&1; then
  echo "[build-wasm] wasm-pack not found — installing via cargo..."
  cargo install wasm-pack
fi

wasm-pack build --release --target web --out-name jumpjump_core --out-dir ../wasm
echo "[build-wasm] done. Files in jumpjump/wasm/"
echo "[build-wasm] index.html will auto-detect the .wasm on next load."
