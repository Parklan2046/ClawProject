# `wasm/` — compiled WASM module lives here

This folder holds the output of `wasm-pack build` (run `../build-wasm.sh` or
`../build-wasm.ps1`). Expected files after a successful build:

- `jumpjump_core.js` — wasm-bindgen JS glue
- `jumpjump_core_bg.wasm` — compiled binary

## If these files are absent

The game still runs. `index.html` attempts to `import()` the module on boot; if
the fetch fails (404) it falls back to the JS `JsCore` implementation, which is
byte-for-byte identical to `wasm-src/src/lib.rs` in behavior. So:

- **Casual users:** no build needed. Open `index.html`.
- **Want WASM speed:** install Rust + `wasm-pack`, run the build script, refresh.

## Verification

The dev console logs one of:
- `[core] using WASM` — WASM loaded successfully
- `[core] using JS fallback` — running on the JS equivalent
