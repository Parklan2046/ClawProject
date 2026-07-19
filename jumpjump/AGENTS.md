# AGENTS.md — jumpjump

跳一跳風格休閒跳躍遊戲。單檔 HTML + Canvas 2D 等距投影 + Rust→WASM 核心邏輯。

## Run

```bash
cd jumpjump/
python -m http.server 8775   # http://127.0.0.1:8775
# or just open index.html directly (file://) — works fine
```

No dependencies, no build step required to **play**. WASM is optional (see below).

## Files

| File | Purpose |
|---|---|
| `index.html` | Single-file: all CSS + JS inline. Game loop, renderer, audio, UI. |
| `wasm-src/` | Rust crate `jumpjump_core` (`wasm-bindgen`, `crate-type = ["cdylib","rlib"]`). Pure game logic. |
| `wasm/` | Output of `wasm-pack build`. May be empty — see WASM section. |
| `build-wasm.sh` / `build-wasm.ps1` | Build the Rust core into `wasm/jumpjump_core_bg.wasm`. |
| `manifest.webmanifest` | PWA manifest. `lang=zh-Hant-HK`, portrait, standalone. |
| `sw.js` | Service worker, versioned cache `jumpjump-v1`, app-shell only. |
| `icon.svg` | Single SVG icon (`any` + `maskable` purpose). |

## Architecture

### WASM with JS fallback (important)

The core game logic (physics, platform-gen, landing detection, scoring) exists
in **two places**:

1. `wasm-src/src/lib.rs` — Rust, compiled to WASM
2. Inside `index.html`, the `JsCore` object — identical-pure JavaScript

On boot, `index.html` does:

```js
const Core = await (async () => {
  try {
    const m = await import('./wasm/jumpjump_core.js');
    await m.default();  // init wasm
    console.log('[core] using WASM');
    return m;
  } catch (e) {
    console.log('[core] using JS fallback', e.message);
    return JsCore;
  }
})();
```

**If you edit game logic, edit both files.** They must produce identical
outputs. There's no test asserting parity — keep functions pure and small.

### JS ↔ WASM contract

All exported Rust functions are `#[wasm_bindgen]` and take/return primitives
or `Vec<f32>` (→ JS `Float32Array`). Return arrays pack multiple values:

| Function | Returns (packed) |
|---|---|
| `compute_jump(sx, sy, charge_ms, dir)` | `[ex, ey, ez, peak_h, dur_s, dist]` |
| `gen_platform(px, py, diff, seed)` | `[x, y, r, shape, dist]` |
| `check_landing(cx, cy, px, py, pr)` | `[kind(0\|1\|2), offset]` |
| `jump_distance(ms)` / `jump_duration(d)` / `jump_height(d)` | scalar |
| `score_for(kind, combo)` / `next_dir(seed)` | scalar |

### Coordinate system

- World coords `(x, y, z)` — `z` is up. Platforms are disks at `z = 0`.
- Iso projection: `sx = (x − y) * cos30`, `sy = (x + y) * sin30 − z`.
- Camera: world is translated so the character stays near vertical center.
- Two jump directions alternate (noise from seed): `(+cos30, +sin30)` and
  `(−cos30, +sin30)` — diagonal hops, faithful to the original.

### Game state shape

Single object `G` (declared inside the IIFE). Persisted slice in
`localStorage.jumpjump_v1`:

```js
{ best: 0, lastScore: 0, muted: false }
```

Bump the `_v1` suffix to invalidate. Never mutate the existing key's shape.

### Tunable constants

Both `lib.rs` and `JsCore` define an identical block of `const`s:

```text
JUMP_SPEED=220  JUMP_MAX_DIST=320  JUMP_MAX_CHARGE_S=1.5
JUMP_PEAK_MIN=60  JUMP_PEAK_MAX=110
PERFECT_RATIO=0.22  GOOD_RATIO=1.0
PLATFORM_BASE_R=42  PLATFORM_R_MIN=24
PLATFORM_BASE_MAX=110  PLATFORM_MAX_DIST_CAP=220
```

## Build WASM

Prereqs: `rustup` + `rustup target add wasm32-unknown-unknown` + `wasm-pack`.

```bash
./build-wasm.sh          # macOS/Linux/Git-Bash
# or
powershell -File build-wasm.ps1
```

Outputs land in `wasm/`. `index.html` detects the new `.wasm` on next reload.

## Mobile

- Viewport: `width=device-width, initial-scale=1, maximum-scale=1,
  user-scalable=no, viewport-fit=cover`
- Pointer Events (`pointerdown`/`pointerup`/`pointermove`) — single path for
  mouse + touch. `touch-action: manipulation` on canvas kills 300ms delay.
- Canvas is DPR-aware (`devicePixelRatio` scaling) and uses `100dvh`.
- `safe-area-inset-*` padding for notched phones.
- PWA-installable on iOS/Android home screen.

## Audio

All SFX synthesized at runtime via Web Audio API (`OscillatorNode` /
`GainNode` / noise buffers). **No asset files.** Toggle via 🔊/🔇 button;
preference persisted in `localStorage.jumpjump_v1.muted`.

## Gotchas

1. **No `server.py`** — this is a pure static project. Don't add a backend
   without a reason; if you do, follow the repo port convention (`:8775` is
   the natural pick, env var `JUMPJUMP_PORT`).
2. **`file://` works** — no module import issues because the WASM fetch fails
   cleanly and falls back to JS. Don't add fetch-based loading that would
   break under `file://`.
3. **Inline JS uses terse identifiers** for size (`G`, `cx`, `dpr`, `t`, `r`).
   This is intentional — matches repo convention. Keep new code terse.
4. **No comments in source** as a rule. Region markers use Unicode dividers:
   `// ═══ SECTION ═══` or `/* ── SECTION ── */`.
5. **UI language is Cantonese (HK).** Keep new strings in the same register
   (撳住蓄力、放手跳、完美、再嚟一次). Server-side logs (none here) would be English.
