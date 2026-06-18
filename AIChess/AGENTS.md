# AGENTS.md

Working notes for AI/agent contributors in this repository.

## Project

**象棋 LLM 競技場 / xiangqi-llm-arena** — a Chinese-Xiangqi (象棋) arena where LLM providers play each other on a 3D board, built with Next.js 15 + React 19 + react-three-fiber. UI is Traditional Chinese.

This is a single-page app with **a test harness, no CI, no lint config** beyond `next lint` defaults, and **no git repo** in this directory.

## Commands

```bash
npm install --legacy-peer-deps   # required: React 19 vs @react-three/drei 9.x peer-dep conflict
npm run dev         # next dev (default :3000)
npm run build       # next build, outputs to ./dist (see next.config.js)
npm start           # next start (production)
npm run lint        # next lint (eslint config not committed; runs with defaults)
```

### Engine QA test harness

A 50-assertion test suite for `lib/xiangqi-engine.ts` lives at `tests/engine.test.ts` and runs on Node 24+ without transpilation via `--experimental-strip-types`:

```bash
node --experimental-strip-types --no-warnings tests/engine.test.ts
```

The harness exercises rook, horse, elephant, advisor, king, cannon, pawn rules; pin, check, checkmate; FEN roundtrip; history; halfmove clock; illegal-move rejection. `tsconfig.json` excludes the `tests/` directory from the main project (use `tests/tsconfig.json` to typecheck the test file).

## Build / runtime gotchas

- `next.config.js` has `output: 'export'` — this is a **static export**. There is no Node server at runtime; everything is client-side. Do not add API routes, `getServerSideProps`, or `next/image` (note `images.unoptimized: true`).
- Build output goes to `dist/` (custom `distDir`), not `.next`.
- Both `typescript.ignoreBuildErrors` and `eslint.ignoreDuringBuilds` are `true`. Type errors and lint warnings will NOT fail the build. Don't rely on `npm run build` to catch type mistakes.
- React 19 + Next 15. JSX is preserved via `jsx: "preserve"` in `tsconfig.json`; never set `noEmit: false` in app code.
- Path alias `@/*` maps to repo root (`./*`). `import { ... } from '@/lib/...'` works for files at `lib/...`.
- Strict mode is on despite the build-ignore flags — type errors still show in IDE / `tsc --noEmit`.

## Code organization

```
app/                Next.js App Router entry
  layout.tsx        Root layout, sets <html lang="zh-Hant">
  page.tsx          Home: wires Scene + GameControls + MoveHistory, runs LLM auto-play loop
  globals.css       Tailwind directives + CSS vars (HSL theme tokens) + thinking animation
lib/
  types.ts          All shared TS types (LLMConfig, GameState, Move, Player, GameConfig, LLMResponse)
  constants.ts      DEFAULT_LLM_CONFIGS, INITIAL_FEN, PIECE_NAMES (Chinese chars), SIDE_NAMES
  xiangqi-engine.ts Minimal board engine (FEN parse/serialize, ASCII render, move gen, makeMove)
  llm-player.ts     LLMPlayer class — wraps OpenAI SDK, prompts the LLM, validates legal-move JSON
hooks/
  useGame.ts        Zustand store. Single source of truth for game state + side effects
components/
  3d/Scene.tsx              Canvas + lights + OrbitControls (camera at [0,12,8], wood env)
  3d/XiangqiBoard3D.tsx     Board mesh + grid + river + palace diagonals + 90 clickable squares
  3d/XiangqiPiece.tsx       Cylindrical piece with CJK glyph (loads /fonts/NotoSansSC-Bold.woff)
  GameControls.tsx          Side panel: choose Red/Black player (human|LLM), start game, API key inputs
  MoveHistory.tsx           Paged move table (red/black columns), latest-move highlight
index.html         26KB ORPHANED static 2D page — NOT used by Next. Safe to delete; do not edit it.
```

### Data flow

1. `app/page.tsx` mounts → `useGame.init()` populates Zustand state from the engine.
2. User clicks "開始對局" in `GameControls` → `useGame.newGame(config)` resets engine + stores `GameConfig`.
3. `app/page.tsx` watches `state.turn` and `config`; when the current side's player is an LLM, it schedules `requestLLMMove()` after `delayBetweenMoves` ms.
4. `requestLLMMove` builds an `LLMPlayer` from the side's `LLMConfig`, sends FEN + ASCII + legal moves to the provider, parses JSON `{move, reasoning}`, validates `move` is in `legalMoves`, and calls `useGame.makeMove(iccs)`.
5. Human turns: click a piece in `XiangqiBoard3D` to select, click a target square to play.

### Board geometry convention (ICCS)

- Files `a..i` (0..8 left→right), ranks `0..9` (red at rank 0, black at rank 9).
- `INITIAL_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1'`
- ICCS move string is 4 chars: `<fromFile><fromRank><toFile><toRank>`, e.g. `e3e4`.
- Engine board: 10 ranks × 9 files, indexed `[rank][file]`. `parseFEN` puts FEN row 0 (top of string) into `board[9]` and row 9 (bottom) into `board[0]`, matching the standard "black-on-top" convention.
- **Pieces are color-coded by case**: uppercase = red (`RNBAKABNR`), lowercase = black (`rnbakabnr`). `isRed = piece === piece.toUpperCase()`.

### Xiangqi engine — rules

`lib/xiangqi-engine.ts` implements the full Xiangqi rule set:

- **Rook (r)**: orthogonal slide, can capture by landing on the blocker; no jump.
- **Horse (n)**: L-shape (1 orthogonal + 1 diagonal). BLOCKED if the orthogonal "horse-leg" square is occupied. No leap.
- **Elephant (b)**: exactly 2 diagonal steps, blocked by the midpoint "elephant-eye", cannot cross the river.
- **Advisor (a)**: 1 step diagonal, confined to the 3×3 palace.
- **King (k)**: 1 step orthogonal, confined to the palace. Flying-general rule enforced.
- **Cannon (c)**: slides orthogonally for non-capture (0 screens). To capture, must jump EXACTLY one intervening piece (the "screen").
- **Pawn (p)**: forward 1 step before crossing the river; sideways + forward after. Never backward.

Other engine features:
- `isLegalMove(game, iccs)` validates bounds, side, legality, and that the king isn't left in check.
- `makeMove(game, iccs)` refuses illegal moves.
- `getGameResult(game)` returns `{ status, winner, reason }` where status is `'playing' | 'checkmate' | 'stalemate' | 'draw'`. Draws are detected on 60-move (no pawn move, no capture) and threefold repetition.
- `getLastMove(game)` returns the captured piece and the moving piece.

`pseudoMovesForPiece` enforces the rules for each piece; `generateLegalMoves` wraps it with an apply→isInCheck→undo filter to remove moves that leave the mover's own king in check.

### LLM client

- Uses the `openai` SDK with `dangerouslyAllowBrowser: true` and arbitrary `baseURL`. Any OpenAI-compatible endpoint (DeepSeek, Qwen, Moonshot, etc.) works without code changes.
- API keys are entered in `GameControls`'s "API Key 設定" panel and stored in `localStorage` under `apiKey_<id>`. `loadConfigWithKeys(base)` reads the stored key and merges it into a `LLMConfig`. `handleStart` blocks "開始對局" if either side's LLM has no key. If `requestLLMMove` is called and the LLM returns an illegal move, the engine falls back to `legalMoves[0]`.
- System prompt includes FEN, ASCII board, and the full legal-move list. `response_format: { type: 'json_object' }` is required — providers that don't support it will error.
- On invalid move / API error, retries up to `maxRetries` (default 3). If all attempts fail, returns `legalMoves[0]` as a fallback.

## Conventions

- **No comments in source files.** Existing files follow this — don't add explanatory comments.
- **Traditional Chinese** in user-facing strings (e.g. `紅方`, `黑方`, `對戰配置`, `開始對局`). Match this when adding UI text.
- **Tailwind utility classes** for styling. Theme tokens come from CSS variables in `app/globals.css` (`--background`, `--primary`, etc.) — don't hardcode colors when a token exists.
- **`'use client';`** at the top of every component that uses hooks, state, browser APIs, or three.js. `app/page.tsx`, all `components/`, and `hooks/useGame.ts` all need it. `app/layout.tsx` is intentionally a server component.
- **Zustand** for state. The store is a flat object with action methods. Components subscribe via `useGame(selector)` or destructure in render.
- **lucide-react** for icons (`Swords`, `Bot`, `User`, `Trophy`, `Play`, `History`, `RotateCcw`, `ChevronLeft/Right`).
- **3D pieces** are cylinders with `<Text>` from `@react-three/drei` for the CJK glyph. Selected piece lifts to y+0.4 via `useFrame` lerp. Font loaded from `/public/fonts/NotoSansSC-Bold.woff` (must exist for glyphs to render).
- **File naming**: PascalCase for components (`XiangqiPiece.tsx`), camelCase for hooks (`useGame.ts`), lowercase for lib (`constants.ts`).

## Adding a new LLM provider

1. Append a new entry to `DEFAULT_LLM_CONFIGS` in `lib/constants.ts` (unique `id`, `provider`, `baseURL`, `model`).
2. Add the new `provider` value to the `LLMConfig.provider` union in `lib/types.ts`.
3. The `LLMPlayer` class needs no changes — any OpenAI-compatible endpoint works.

## Adding new piece rules / fixing the engine

`lib/xiangqi-engine.ts` is the only file to touch. The `generateLegalMoves` switch in that file is the place to add cases for `n` (horse with leg blocking), `b` (elephant, eye blocking, river), `a` (advisor, palace), `k` (king, palace, no face-to-face on same file), `c` (cannon, jump capture). `getGameStatus` needs a real implementation for `checkmate`/`stalemate`/`draw`.

## Things that look broken but are intentional / leftover

- `index.html` (26KB 2D vanilla-JS version) is **not wired to Next**. Next won't serve it. Safe to delete, or move it to `public/` if a static fallback is desired.
- `components/3d/` uses the `@react-three/fiber` 8.x API; `Scene.tsx` imports it as `Canvas` — fine. Note that `@react-three/drei` 9.x declares a peer dep of React 18, which conflicts with this project's React 19; we install with `--legacy-peer-deps` and runtime works. The Next.js production build **fails at prerender time** with `Cannot read properties of undefined (reading 'ReactCurrentBatchConfig')` from the react-three stack; run `npm run dev` for local play, or expect to ship a CSR-only bundle if the prerender issue isn't fixed upstream.
- `app/page.tsx` `handleStartGame` callback ignores its `gameConfig` argument and only sets `gameStarted`. The actual config is stored via `useGame.newGame(config)` from `GameControls`.
- `requestLLMMove` catches errors, sets `errorMessage` on the store (rendered as a dismissible red banner at the top of the page), and falls back to `legalMoves[0]` so the game keeps progressing.
- `next.config.js` has both `typescript.ignoreBuildErrors: true` and `eslint.ignoreDuringBuilds: true`. Don't expect the build to surface type errors. Run `node ./node_modules/typescript/bin/tsc --noEmit -p tsconfig.json` separately.
