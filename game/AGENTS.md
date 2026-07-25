# AGENTS.md — 逆命大郎 (Godot web game)

A Godot 4.7 wuxia narrative game, web-export only. A modern Hong Kong
restaurant owner dies and wakes as 武大郎 (Wu Dalang) in Song-dynasty 陽谷縣,
trying to rewrite a doomed fate. The prologue is the only playable content so far;
later chapters are stubbed.

All UI text and dialogue are **Traditional Chinese with Cantonese phrasing**.
Match this when writing player-facing strings.

## Commands

- **Run**: open `project.godot` in Godot 4.7.1 and press Play. Main scene is
  `res://scenes/login.tscn`.
- **Export web** (requires matching export templates installed):
  ```powershell
  godot --headless --path . --export-release Web web/index.html
  ```
- **Serve the export**: the `web/` directory must be served over HTTP/HTTPS.
  Opening `web/index.html` via `file://` does **not** work (wasm/threads/audio
  all blocked). There is no committed dev-server script; use any static server.
- **No tests, no linter, no formatter** exist in this project. Do not invent
  `npm run test` / `godot --headless --check` CI commands — verify any GDScript
  change by running the project in the editor.

## Architecture

### Autoloads (global singletons, declared in `project.godot`)
- `GameState` → `scripts/core/game_state.gd`: player data (name, origin,
  principle, copper, reputation, `relationship` dict, `flags` dict, chapter,
  checkpoint). Owns the canonical `ORIGINS` / `PRINCIPLES` lookup tables and
  `serialize()` / `restore()` for save/load.
- `SaveManager` → `scripts/core/save_manager.gd`: JSON save to
  `user://niming_save_v1.json` (pretty-printed, `version: 1`). Note the path is
  versioned — bump the filename if the schema changes.

Access these as `GameState.foo` / `SaveManager.save_game()` from anywhere;
do **not** instantiate them.

### Scene flow
`login.tscn` → (on success) `change_scene_to_file("res://scenes/prologue.tscn")`
→ prologue ends on a disabled "進入第一章" button (chapter 1 not built).

## Critical conventions & gotchas

### 1. Scenes are stubs — everything is built in code
The `.tscn` files contain **only a root node + script reference** (see
`scenes/login.tscn`, `scenes/prologue.tscn`). All UI, 3D meshes, lights, and
layouts are constructed procedurally in `_ready()` via `*_build_*()` methods.

- Do **not** add nodes in the Godot editor expecting them to persist — the scene
  files are intentionally minimal. Build new UI in GDScript following the
  existing `_build_*` helpers (`_button`, `_box`, `_panel_style`, `_field_label`,
  `_line_edit`, `_spacer`).
- 3D worlds (`town_3d.gd`, `prologue_world.gd`) assemble whole environments from
  primitive meshes using `_box()`, `_cylinder()`, `_sphere()`, `_label_3d()`,
  `_add_omni()`, `_material()`. Reuse these helpers instead of loading `.glb`
  models — the project ships no 3D asset files.

### 2. Web audio is played by the HTML shell, not Godot
`assets/audio/guzheng-theme.mp3` is **excluded from the web export** (see
`export_presets.cfg` `exclude_filter`). On web, `wuxia_ost.gd` does **not** use
`AudioStreamPlayer` — it drives an `<audio id="niming-ost">` element living in
`web_shell.html` via `JavaScriptBridge.eval`. This is required to satisfy
browser autoplay policies (audio must resume after a user gesture).

- If you add audio for web, follow the same pattern or it will be silent.
- Native (editor/desktop) builds *do* load the mp3 via `AudioStreamPlayer`.
- The OST's class name is `WuxiaOST`; `WuxiaTown3D` is the login viewport's
  class name. These `class_name` declarations are load-bearing for typed
  `preload()` + `.new()` instantiation.

### 3. `export_presets.cfg` excludes most assets from the web build
The `exclude_filter` drops: all `assets/bg/*.jpg` **except** `town-hybrid.jpg`,
all `assets/girls/*`, `assets/audio/guzheng-theme.mp3`, and the entire `web/*`
output dir. If you reference a new background image or girl portrait from
GDScript, **add it to the include path or remove it from the exclude list** or
the web build will fail to load it at runtime (desktop editor will still work,
masking the bug).

### 4. `prefers-reduced-motion` gating
Both scenes read `window.matchMedia('(prefers-reduced-motion: reduce)')` via
`JavaScriptBridge.eval` on web (returns `false` off-web) and store it in a
`reduce_motion` bool. **Every tween, intro animation, and typing effect must be
gated** behind `if not reduce_motion:` — see `_play_intro`, `_advance_line`,
`_cross_to_song`, `_show_error`. Skipping this breaks accessibility.

### 5. Dialogue & choice flow is a callback chain
Story beats are linear functions that call `_run_lines([...], next_callback)`:
- `_run_lines` shows the dialogue panel and types each line via a
  `RichTextLabel.visible_ratio` tween. A click skips the typing first, then
  advances; on the last line it calls the callback.
- Choices use `_show_choices(title, options)` where each option is
  `{label, description, action}`. The `action` is usually a `Callable.bind(id)`
  that writes to `GameState` (flags / relationship) then chains to the next
  `_run_lines`.
- To extend the story, add a new `_next_beat()` function and pass it as the
  callback of the preceding beat. Do not fork the chain; it is intentionally
  linear.

### 6. Game state is mutated in place during the prologue
Choices mutate `GameState.relationship`, `GameState.flags`, `GameState.reputation`
directly. `GameState.set_flag(key, value)` / `get_flag(key, fallback)` is the
flag API. The prologue calls `SaveManager.save_game()` once at the end
(`_repair_finished`); mid-prologue state is not persisted. `GameState.reset_prologue()`
runs at prologue `_ready()` — re-entering the scene wipes progress.

### 7. Responsive layout is manual positioning
There are no anchor/container-based layouts for the major panels. Each scene
implements `_apply_layout()` (connected to `viewport.size_changed`) that
manually sets `.position` and `.size` for every panel, branching on a mobile
breakpoint (`viewport.x < 760` in both scenes; prologue also tracks
`compact := viewport.y < 600`). When adding a panel, you must add positioning
for it in **both** the mobile and desktop branches of `_apply_layout`, or it
will render at `(0,0)`.

**Mobile font convention:** any text a player reads on a phone must be ≥16px
for body/dialogue/inputs and ≥14px absolute floor for secondary text — CJK
glyphs are unreadable below this. Every `add_theme_font_size_override` set in
the mobile branch MUST be mirrored with a reset in the desktop `else` branch
(the override persists across viewport resizes). Prologue tracks `mobile` and
`compact` as instance vars (set in `_apply_layout`, read in `_show_summary` and
`_show_choices`) so size/height can adapt at creation time. The `timing_gauge`
draws text directly via `draw_string` and branches its hint string on
`size.x < 320` to avoid clipping on narrow screens.

### 8. Timing-gauge mini-game (`scripts/ui/timing_gauge.gd`)
A self-contained `Control` that draws itself via `_draw()` (oscillating needle,
golden target zone). Call `gauge.start(rounds)`, listen for the `finished(score)`
signal (0.0–1.0). Input handled via `_gui_input` (mouse/touch) and
`_unhandled_key_input` (`ui_accept` / space). It is reused, not subclassed.

## File map

```
project.godot              # Godot 4.7 config: autoloads, GL Compatibility renderer, 1440x900
export_presets.cfg         # single "Web" preset, custom shell, big exclude_filter
web_shell.html             # custom HTML shell: branded loader + the <audio id="niming-ost"> element
GODOT.md                   # short human-oriented project note (read this too)
scripts/
  core/        game_state.gd, save_manager.gd   # autoloads
  login.gd     # Control scene: hybrid painted-2D + real-time-3D town + login form
  town_3d.gd   # WuxiaTown3D: SubViewport rendering a procedural Song-dynasty street (login backdrop)
  wuxia_ost.gd # WuxiaOST: AudioStreamPlayer (native) / JSBridge-to-<audio> (web)
  prologue/
    prologue.gd       # Node3D scene: dialogue, choices, inspection, repair mini-game, summary
    prologue_world.gd # builds modern-restaurant + Song-home 3D sets; camera focus tweening
  ui/
    timing_gauge.gd   # the "修爐火候" timing mini-game
scenes/        login.tscn, prologue.tscn   # stub scenes, script-only
assets/        bg/, girls/, fonts/, audio/  (see export exclude_filter before adding references)
web/           # export OUTPUT — regenerated, do not hand-edit
```

### Legacy files (do not treat as live code)
Root-level `index.html`, `login.html`, `login.css`, `login.js`, `login-scene.js`,
`wuxia-game.html` are the **pre-Godot HTML prototype** that the Godot project
migrated from (per `GODOT.md`: "This folder is *now also* a Godot project").
The Godot build is the source of truth. Avoid editing these unless explicitly
modernizing the prototype.

### `.gd.uid` files are committed on purpose
Godot 4 generates `<script>.gd.uid` files to track stable resource IDs across
renames. They are **not** gitignored here — commit them alongside their `.gd`
files. Do not delete or hand-edit them.

## Rendering notes
- Renderer is `gl_compatibility` (desktop + mobile) for Mobile Safari support.
  Do not switch to Forward+/Mobile-only features (cluster lights, etc.) without
  re-testing the web export.
- Viewport default 1440x900, `window/stretch/mode = "disabled"` (no auto-stretch;
  scenes handle their own layout via `_apply_layout`).
- Font: `assets/fonts/NotoSansTC-Variable.ttf`, loaded per-scene into a fresh
  `Theme` with MSDF enabled in `project.godot`.

## Style
- Tabs for indentation in GDScript (Godot convention).
- Private helpers prefixed `_`; `const` lookups in `UPPER_SNAKE`; colors as
  hex `Color("#rrggbb")` module constants (e.g. `TEXT`, `MUTED`, `ACCENT`,
  `GOLD`, `RED`, `INK`).
- Typed where practical: `-> void`, `:=` inference, `Array[Type]` for typed
  arrays (`var warm_lights: Array[OmniLight3D]`).
