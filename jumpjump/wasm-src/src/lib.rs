/* ═══ jumpjump_core — WASM core for 跳一跳 ═══
 * Pure, deterministic game logic. No side effects, no global state.
 * The browser JS layer (../index.html) ships a byte-for-byte equivalent
 * fallback (JsCore) so the game runs even without a WASM build.
 *
 * All functions return primitives or Vec<f32> (-> JS Float32Array).
 * Packed return shapes are documented per-fn.
 */

use wasm_bindgen::prelude::*;

const COS30: f32 = 0.866_025_4;
const SIN30: f32 = 0.5;

const JUMP_SPEED: f32 = 220.0;
const JUMP_MAX_DIST: f32 = 320.0;
const JUMP_MAX_CHARGE_S: f32 = 1.5;
const JUMP_PEAK_MIN: f32 = 60.0;
const JUMP_PEAK_MAX: f32 = 110.0;
const JUMP_BASE_TIME: f32 = 0.35;
const JUMP_TIME_PER_DIST: f32 = 0.001_2;

const PERFECT_RATIO: f32 = 0.22;
const GOOD_RATIO: f32 = 1.0;

const DIR_AX: f32 = 0.866_025_4;
const DIR_AY: f32 = 0.5;
const DIR_BX: f32 = -0.866_025_4;
const DIR_BY: f32 = 0.5;

const PLATFORM_BASE_R: f32 = 42.0;
const PLATFORM_R_SHRINK: f32 = 0.18;
const PLATFORM_R_MIN: f32 = 24.0;
const PLATFORM_MIN_DIST: f32 = 70.0;
const PLATFORM_BASE_MAX: f32 = 110.0;
const PLATFORM_MAX_DIST_CAP: f32 = 220.0;
const PLATFORM_DIST_PER_DIFF: f32 = 2.5;

#[inline]
fn xorshift(state: &mut u32) -> u32 {
    let mut x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    x
}

#[wasm_bindgen]
pub fn iso_cos30() -> f32 { COS30 }

#[wasm_bindgen]
pub fn iso_sin30() -> f32 { SIN30 }

#[wasm_bindgen]
pub fn jump_distance(charge_ms: f32) -> f32 {
    let t = (charge_ms / 1000.0).min(JUMP_MAX_CHARGE_S).max(0.0);
    (t * JUMP_SPEED).min(JUMP_MAX_DIST).max(0.0)
}

#[wasm_bindgen]
pub fn jump_duration(distance: f32) -> f32 {
    JUMP_BASE_TIME + distance * JUMP_TIME_PER_DIST
}

#[wasm_bindgen]
pub fn jump_height(distance: f32) -> f32 {
    let r = (distance / JUMP_MAX_DIST).clamp(0.0, 1.0);
    JUMP_PEAK_MIN + (JUMP_PEAK_MAX - JUMP_PEAK_MIN) * r
}

/* compute_jump -> [end_x, end_y, end_z, peak_h, duration_s, distance] */
#[wasm_bindgen]
pub fn compute_jump(start_x: f32, start_y: f32, charge_ms: f32, dir_index: u32) -> Vec<f32> {
    let d = jump_distance(charge_ms);
    let (dx, dy) = if dir_index & 1 == 0 { (DIR_AX, DIR_AY) } else { (DIR_BX, DIR_BY) };
    vec![
        start_x + dx * d,
        start_y + dy * d,
        0.0,
        jump_height(d),
        jump_duration(d),
        d,
    ]
}

/* gen_platform -> [plat_x, plat_y, radius, shape(0=round|1=square), dist_from_prev] */
#[wasm_bindgen]
pub fn gen_platform(prev_x: f32, prev_y: f32, difficulty: u32, seed: u32) -> Vec<f32> {
    let mut s = seed
        .wrapping_mul(2654435761)
        .wrapping_add(2654435769)
        .wrapping_add(difficulty.wrapping_mul(7));
    if s == 0 { s = 0x12345678; }
    let _ = xorshift(&mut s);

    let choice = xorshift(&mut s) & 1;
    let (dx, dy) = if choice == 0 { (DIR_AX, DIR_AY) } else (DIR_BX, DIR_BY);

    let max_d = (PLATFORM_BASE_MAX + difficulty as f32 * PLATFORM_DIST_PER_DIFF)
        .min(PLATFORM_MAX_DIST_CAP);
    let r01 = xorshift(&mut s) as f32 / u32::MAX as f32;
    let dist = PLATFORM_MIN_DIST + (max_d - PLATFORM_MIN_DIST) * r01;

    let shrink = (difficulty as f32 * PLATFORM_R_SHRINK).min(PLATFORM_BASE_R - PLATFORM_R_MIN);
    let radius = PLATFORM_BASE_R - shrink;

    let shape = xorshift(&mut s) & 1;

    vec![prev_x + dx * dist, prev_y + dy * dist, radius, shape as f32, dist]
}

/* check_landing -> [kind(0=miss|1=good|2=perfect), offset_from_center] */
#[wasm_bindgen]
pub fn check_landing(char_x: f32, char_y: f32, plat_x: f32, plat_y: f32, plat_r: f32) -> Vec<f32> {
    let off = ((char_x - plat_x).powi(2) + (char_y - plat_y).powi(2)).sqrt();
    let kind = if off > plat_r * GOOD_RATIO { 0u32 }
               else if off < plat_r * PERFECT_RATIO { 2u32 }
               else { 1u32 };
    vec![kind as f32, off]
}

#[wasm_bindgen]
pub fn score_for(kind: u32, combo: u32) -> u32 {
    match kind {
        2 => 2 + combo.min(20),
        1 => 1,
        _ => 0,
    }
}

/* next_dir: deterministic alternating-but-noisy direction index from seed */
#[wasm_bindgen]
pub fn next_dir(seed: u32) -> u32 {
    let mut s = seed.wrapping_add(0xABCDEF);
    if s == 0 { s = 1; }
    (xorshift(&mut s) & 1) as u32
}
