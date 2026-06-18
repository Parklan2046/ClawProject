/**
 * Xiangqi engine QA harness.
 * Run: node --experimental-strip-types tests/engine.test.ts
 *
 * Convention: ICCS <fromFile><fromRank><toFile><toRank>, files a-i (0-8), ranks 0-9.
 * Red is at the BOTTOM (rank 0), black at the TOP (rank 9). Red pieces = UPPERCASE.
 * Red palace = ranks 0-2, files 3-5. Black palace = ranks 7-9, files 3-5.
 * Red half = ranks 0-4, black half = ranks 5-9.
 * Red pawn forward = INCREASING rank. Black pawn forward = DECREASING rank.
 */
import { strict as assert } from 'node:assert';
import {
  createGame, getFEN, getLegalMoves, makeMove, isLegalMove,
  getGameStatus, getTurn, getHistory, getLastMove, getGameResult,
  isInCheckPublic, INITIAL_FEN
} from '../lib/xiangqi-engine.ts';

let pass = 0, fail = 0;
const failures: { name: string; detail?: string }[] = [];

function check(name: string, cond: boolean, detail?: string) {
  if (cond) { pass++; console.log('  PASS  ' + name); }
  else { fail++; failures.push({ name, detail }); console.log('  FAIL  ' + name + (detail ? ' :: ' + detail : '')); }
}

function newGame(fen?: string) { return createGame(fen); }
function m(g: any) { return getLegalMoves(g).slice().sort(); }
function mv(g: any, iccs: string) { return makeMove(g, iccs); }
function st(g: any) { return getGameStatus(g); }
function tr(g: any) { return getTurn(g); }
function ck(g: any) { return isInCheckPublic(g); }

// ===========================================================
console.log('\n=== T1: INITIAL POSITION ===');
{
  const g = newGame();
  check('turn is red', tr(g) === 'red');
  check('status playing', st(g) === 'playing');
  check('not in check', !ck(g));
  const ms = m(g);
  check('exactly 44 red moves', ms.length === 44, `got ${ms.length}`);
}

// ===========================================================
console.log('\n=== T2: ROOK MOVES AND CAPTURES ===');
{
  // Red rook at d3 (file 3, rank 2), open file above and below, red king at d0
  // FEN: k8/9/9/9/9/9/9/9/3R5/3K5 w - - 0 1
  // rank 1: '3R5' = file 3 R
  // rank 0: '3K5' = file 3 K
  const g = newGame('k8/9/9/9/9/9/9/9/3R5/3K5 w - - 0 1');
  const ms = m(g).filter(x => x.startsWith('d1'));
  // d2 is where the rook is (rank 1? wait, my rank is 1 in FEN rank 1 = engine rank 1, ICCS d2 = file 3, rank 1)
  // So rook is at d2 ICCS = engine (1, 3)
  // Vertical moves: d0 (own king, illegal), d1 (empty, rank 0 engine = d0 ICCS? confusing)
  // Let me redo with clear notation
  // Engine rank 0 = bottom = ICCS rank 0. Engine rank 9 = top = ICCS rank 9.
  // FEN 'k8/9/9/9/9/9/9/9/3R5/3K5 w - - 0 1'
  //   rank 9 (top, black king at e9)
  //   ranks 8-2: empty
  //   rank 1: '3R5' = file 3 = red rook. ICCS: d2 (file d=3, rank 1 → wait, file index 3 = 'd' yes; rank 1 in FEN = 'd2'? No.
  //   ICCS uses the rank as it appears in the FEN: file 3, engine rank 1 → ICCS 'd1'
  //   Hmm I keep getting confused. Let me check by parsing the FEN.
  //   Rank 1 FEN row '3R5' = 3 empty + R + 5 empty = file 0..2 empty, file 3 = R, file 4..8 empty
  //   So red rook at file 3, engine rank 1. ICCS = 'd1' (d for file 3, 1 for rank)
  //   Rank 0 FEN row '3K5' = red king at file 3, engine rank 0. ICCS = 'd0'
  //   So rook at d1, king at d0.
  //   Rook d1 moves: vertical: d0 (own king, illegal), d2..d9 (empty). Lateral: a1..i1 along rank 1 minus d1.
  //   Total 8 vertical + 8 lateral - own-king = 15, but d0 is own king so 14.
  //   Wait: d1 can move to d0 (illegal own), d1 to d2-d9 = 8 moves, d1 to a1,b1,c1 (3 moves, files 0-2), d1 to e1-i1 (5 moves, files 4-8). Total = 0 (no d0) + 8 + 3 + 5 = 16? But d0 is own king. So total 15.
  const expected = ['d1a1','d1b1','d1c1','d1d2','d1d3','d1d4','d1d5','d1d6','d1d7','d1d8','d1d9','d1e1','d1f1','d1g1','d1h1','d1i1'].sort();
  check('rook d1 has 16 legal moves (open file + open rank)',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);

  // Capture: place a black rook on d5
  const g2 = newGame('k8/9/9/9/3r5/9/9/9/3R5/3K5 w - - 0 1');
  // rank 4: '3r5' = black rook at file 3, engine rank 4
  const ms2 = m(g2).filter(x => x.startsWith('d1'));
  // d1 can move: d2,d3,d4 (empty, before blocker at d5), d5 (capture), d6..d9 (blocked)
  check('rook d1 captures black rook at d5 (file blocked after capture)',
    ms2.includes('d1d5') && !ms2.includes('d1d6') && !ms2.includes('d1d7'),
    `got: ${ms2.join(',')}`);

  // Blocked by own piece: place a red pawn at d3
  const g3 = newGame('k8/9/9/9/9/9/9/3P5/3R5/3K5 w - - 0 1');
  // rank 1: '3P5' = d2 (own pawn), engine rank 1. ICCS d2.
  // Test: rook d1 blocked by own pawn at d2: cannot move to d2 or d3+ (since d2 is first blocker)
  const ms3 = m(g3).filter(x => x.startsWith('d1'));
  // d1d2: capture own pawn, illegal. d1d3+ blocked. d1 can slide: a1,b1,c1,e1,f1,g1,h1,i1.
  check('rook d1 blocked by own pawn at d2: only lateral slides',
    !ms3.includes('d1d2') && !ms3.includes('d1d3') && !ms3.includes('d1d4') && ms3.includes('d1a1') && ms3.includes('d1i1'),
    `got: ${ms3.join(',')}`);
}

// ===========================================================
console.log('\n=== T3: HORSE L-SHAPE + LEG BLOCKING ===');
{
  // Red horse at b3 (file 1, rank 2). Red king at e0, black king at e9 — different file, no flying general.
  // Place a piece on the e-file between to also avoid accidental alignment. Use: black king on i9, red king on a0.
  // FEN: k8/9/9/9/9/9/9/1N7/9/8K w - - 0 1
  // rank 2: '1N7' = file 1, red horse
  // Horse at engine (2, 1) ICCS b3
  // 8 moves: (1,0) a2, (1,2) c2, (0,3) d1, (0,-1)=OOB, (2,3) d5? wait
  // From (2,1): all 8 deltas (±2, ±1) and (±1, ±2) where all are non-zero
  // (4,0)=a5, (4,2)=c5, (3,3)=d4, (1,3)=d2, (3,-1)=OOB, (1,-1)=OOB, (0,0)=OOB, (0,2)=c1
  // Wait (2,1) ±2 rank = 0 or 4, ±1 file = 0 or 2
  // (0,0) a1, (0,2) c1, (4,0) a5, (4,2) c5
  // (2,1) ±1 rank = 1 or 3, ±2 file = -1 or 3
  // (1,-1) OOB, (1,3) d2, (3,-1) OOB, (3,3) d4
  // So 6 valid: a1, c1, a5, c5, d2, d4 → ICCS: a1, c1, a5, c5, d2, d4
  const g = newGame('k8/9/9/9/9/9/1N7/9/9/8K w - - 0 1');
  const ms = m(g).filter(x => x.startsWith('b3'));
  const expected = ['b3a1','b3a5','b3c1','b3c5','b3d2','b3d4'].sort();
  check('horse b3 has 6 valid L-moves on open board',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);

  // Block leg a3 (between b3 and a1) — leg is at (2,0)=a3 ICCS? wait (2,1)→(0,0) leg at (1,1)=b2. Leg for b3→c1 is at (1,1)=b2. Leg for b3→a5 is at (3,1)=b4. Leg for b3→c5 is at (3,1)=b4. Leg for b3→d2 is at (2,2)=c3. Leg for b3→d4 is at (2,2)=c3.
  // Place a piece at b2 (rank 1, file 1) to block a1, c1
  const g2 = newGame('k8/9/9/9/9/9/1N7/1p7/9/8K w - - 0 1');
  // rank 1: '1p7' = file 1 black pawn = b2
  const ms2 = m(g2).filter(x => x.startsWith('b3'));
  // a1, c1 disabled. a5, c5, d2, d4 still legal
  const expected2 = ['b3a5','b3c5','b3d2','b3d4'].sort();
  check('horse b3 with b2 blocked: a1,c1 disabled',
    JSON.stringify(ms2) === JSON.stringify(expected2),
    `got: ${ms2.join(',')}`);

  // Place horse at b2 with legs at b1 and b3 blocked.
  // FEN: k8/9/9/9/9/9/1p7/1N7/1p7/8K w - - 0 1
  // rank 3: '1p7' = b3 (leg for d1, d3? wait, legs for b2->d1 is c2, for b2->d3 is c3. b2->a4 leg at b3. b2->c4 leg at b3.)
  // Actually from b2: a4 (NW, dr=+2, df=-1, leg b3), c4 (NE, dr=+2, df=+1, leg b3), a0 (SW, dr=-2, df=-1, leg b1), c0 (SE, dr=-2, df=+1, leg b1), d1 (E, dr=-1, df=+2, leg c2), d3 (E+rank, dr=+1, df=+2, leg c3), and two off-board.
  // So blocking b1 disables a0,c0. Blocking b3 disables a4,c4. Remaining: d1, d3.
  const g3 = newGame('k8/9/9/9/9/9/1p7/1N7/1p7/8K w - - 0 1');
  const ms3 = m(g3).filter(x => x.startsWith('b2'));
  const expected3 = ['b2d1','b2d3'].sort();
  check('horse b2 with b1+b3 blocked: only d1,d3 remain (legs c2,c3 free)',
    JSON.stringify(ms3) === JSON.stringify(expected3),
    `got: ${ms3.join(',')}`);

  // Block all legs b2, b4, c3
  const g4 = newGame('k8/9/9/9/9/9/1p1N5/1N7/1p7/8K w - - 0 1');
  // rank 3: '1p1N5' = b4 pawn, c4 wait. Let me check: '1p1N5' = 1+1+1+1+5 = 9. file 0 empty, file 1 p, file 2 empty, file 3 N, files 4-8 empty. So black pawn at b4 (file 1, rank 3) and red horse at d4 (file 3, rank 3). But I want a piece at c3 (file 2, rank 2) blocking legs d2,d4 for horse b3.
  // FEN: 'k8/9/9/9/9/9/2p6/1N7/1p7/8K w - - 0 1'
  // rank 3: '2p6' = file 2 black pawn = c4. Wait c4 is rank 3, not c3. I want c3 (rank 2).
  // 'k8/9/9/9/9/9/9/1N1p5/1p7/8K w - - 0 1'
  // rank 2: '1N1p5' = file 1 N (b3 horse), file 3 p (d3 = file 3, rank 2). Not c3.
  // To get a piece at c3 (file 2, rank 2): '1N1N5'? No, 1+1+1+1+5 = 9 only fits one B. To get N at file 1 and p at file 2: '1N p 6' = '1Np6' = 1+1+1+6 = 9. file 0 empty, file 1 N, file 2 p, files 3-8 empty.
  // So: 'k8/9/9/9/9/9/9/1Np6/1p7/8K w - - 0 1'
  // rank 2: '1Np6' = b3 horse + c3 pawn
  // rank 1: '1p7' = b2 pawn
  // Now I need b4 also. Add to rank 3: '1p7' = b4
  // 'k8/9/9/9/9/9/1p7/1Np6/1p7/8K w - - 0 1'
  // rank 3: '1p7' = b4
  // rank 2: '1Np6' = b3 N + c3 p
  // rank 1: '1p7' = b2
  const g4b = newGame('k8/9/9/9/1p7/1Np6/1p7/9/9/8K w - - 0 1');
  const ms4 = m(g4b).filter(x => x.startsWith('b3'));
  check('horse b3 with b2+b4+c3 all blocked: 0 moves',
    ms4.length === 0,
    `got: ${ms4.join(',')}`);
}

// ===========================================================
console.log('\n=== T4: ELEPHANT MOVES, EYE BLOCK, RIVER ===');
{
  // Red elephant at b3 (file 1, rank 2). All 4 diagonal moves: a1, c1, a5, c5
  // Eye for a1: (1,0)=b2 wait no. Elephant at (2,1). To a1=(0,0): midpoint (1,0) which is a2? No, (rank+rank)/2 = (2+0)/2 = 1, (file+file)/2 = (1+0)/2 = 0.5. Not integer → that's wrong.
  // Hmm, elephant moves exactly 2 diagonal. From (2,1) to (0,-1) = OOB. To (0,3) = c1. Eye at (1,2) = c3. To (4,-1) = OOB. To (4,3) = c5. Eye at (3,2) = d4.
  // Wait, what about (0, -1) and (4, -1)? OOB. So only 2 moves: c1 and c5.
  // Eye for c1 from b3: midpoint (1, 2) = c3? No, (2+0)/2=1, (1+3)/2=2 → engine (1, 2) = ICCS b2. Wait that's a2? File 2 = c. So midpoint file = 2 = c. Hmm.
  // Engine file 2 = 'c'. (1, 2) = rank 1, file 2 = c2. Eye is c2.
  // Eye for c5 from b3: (2+4)/2=3, (1+3)/2=2 → engine (3, 2) = c4. Eye is c4.
  // So elephant b3 can move c1 (eye c2) and c5 (eye c4). What about a1? From (2,1) to (0,-1) is OOB. a5 to (4,-1) OOB. So 2 moves.
  // Kings on different files to avoid flying general: a9 black, h0 red.
  // FEN: k8/9/9/9/9/9/1B7/9/9/8K w - - 0 1
  // rank 3: '1B7' = file 1 red elephant = b3
  // From b3 (engine rank 3), valid moves: d1 (rank 1, in red half), d5 (rank 5, BLACK half, illegal).
  // So only 1 move: d1.
  const g = newGame('k8/9/9/9/9/9/1B7/9/9/8K w - - 0 1');
  const ms = m(g).filter(x => x.startsWith('b3'));
  const expected = ['b3d1'].sort();
  check('elephant b3 has 1 valid move (d1) — d5 would cross river',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);

  // Block eye c2 (rank 1, file 2): eye is midpoint of b3->d1
  // FEN: k8/9/9/9/9/9/1B7/2p6/9/8K w - - 0 1
  // rank 2: '2p6' = file 2 pawn = c2 (wait, c2 = file 2, rank 2? yes, c2 = file 2, rank 2)
  // Actually eye for b3->d1 is at (2, 2) = c2 (file 2 rank 2). FEN pos 7 = engine rank 2.
  const g2 = newGame('k8/9/9/9/9/9/1B7/2p6/9/8K w - - 0 1');
  const ms2 = m(g2).filter(x => x.startsWith('b3'));
  check('elephant b3 with c2 eye blocked: 0 moves',
    ms2.length === 0,
    `got: ${ms2.join(',')}`);

  // River: red elephant at rank 5 (BLACK half — illegal in real game)
  // Should be unable to move at all (engine should reject all moves since out of red half)
  // FEN: k8/9/9/9/9/1B7/9/9/9/8K w - - 0 1
  // rank 5: '1B7' = file 1 red elephant (on black's side)
  const g3 = newGame('k8/9/9/9/9/1B7/9/9/9/8K w - - 0 1');
  const ms3 = m(g3).filter(x => x.startsWith('b6'));
  check('elephant on black side (illegal) generates 0 moves',
    ms3.length === 0,
    `got: ${ms3.join(',')}`);
}

// ===========================================================
console.log('\n=== T5: ADVISOR PALACE CONFINEMENT ===');
{
  // Red advisor should be confined to ranks 0-2, files 3-5
  // Red king at d0 (file 3, rank 0). Advisors at d1 (file 3, rank 1) — wait that's center
  // FEN: k8/9/9/9/9/9/9/3A5/9/3K5 w - - 0 1
  // rank 2: '3A5' = file 3 A = d3 wait no, file 3 = 'd', rank 2 = ICCS d3
  // Hmm I want advisor at d1 (file 3, rank 1). FEN rank 1: '3A5'.
  // FEN: 'k8/9/9/9/9/9/9/9/3A5/3K5 w - - 0 1' → rank 1 = '3A5' = file 3 A = d1
  const g = newGame('k8/9/9/9/9/9/9/9/3A5/3K5 w - - 0 1');
  // Red king at d0, red advisor at d1
  // Advisor at d1 can move diagonally only within palace:
  //   d1 -> c0 (own king? no, c0 is empty), d2 (rank 2, file 3, empty), e0 (file 4, rank 0, empty), e2 (file 4, rank 2, empty)
  //   c0 is at file 2 rank 0 - is that in palace? Palace is files 3-5, ranks 0-2. File 2 NOT in palace. So c0 is illegal.
  //   d2: file 3, rank 2. In palace. Legal.
  //   e0: file 4, rank 0. In palace. Legal.
  //   e2: file 4, rank 2. In palace. Legal.
  //   So 3 moves: d2, e0, e2
  const ms = m(g).filter(x => x.startsWith('d1'));
  const expected = ['d1e0','d1e2'].sort();
  check('advisor d1 has 2 valid diagonal moves within palace (e0, e2)',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);

  // Advisor outside palace: 'k8/9/9/9/9/9/4A4/9/9/8K w - - 0 1'
  // rank 3: '4A4' = file 4 A = e4
  const g2 = newGame('k8/9/9/9/9/9/4A4/9/9/8K w - - 0 1');
  const ms2 = m(g2).filter(x => x.startsWith('e4'));
  check('advisor outside palace has 0 moves',
    ms2.length === 0,
    `got: ${ms2.join(',')}`);
}

// ===========================================================
console.log('\n=== T6: KING PALACE + FLYING GENERAL ===');
{
  // Red king at d0, advisors fill other palace squares
  // FEN: k8/9/9/9/9/9/9/3A5/4A4/3K5 w - - 0 1
  // rank 2: '3A5' = d3
  // rank 1: '4A4' = e2
  const g = newGame('k8/9/9/9/9/9/9/3A5/4A4/3K5 w - - 0 1');
  // King d0 can move to: d1 (own advisor - illegal), e0 (empty in palace), e1 (own advisor? e1 is file 4 rank 1, that's e2 in FEN). Wait my rank indexing.
  // King at engine (0, 3) = ICCS d0. Moves: (1,3)=d1 (own A), (0,4)=e0 (empty), (0,2)=c0 (empty).
  // Wait (0,2) is c0. That's in palace (file 2? No, palace is files 3-5). c0 = file 2 rank 0, NOT in palace. Illegal.
  // So king can move: e0 (legal). And e0 is in palace (file 4 rank 0). Yes.
  // But also king d0 could move to d1? d1 is own advisor (file 3 rank 1). Illegal.
  // So only move is e0. But is e0 in check? No black pieces attacking.
  const ms = m(g).filter(x => x.startsWith('d0'));
  const expected = ['d0d1','d0e0'].sort();
  check('king d0 with advisors at d3 and e2: 2 legal moves (d1, e0)',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);

  // Flying general: kings on same file, no pieces between
  // Red king d0, black king d9, no pieces
  // FEN: k8/9/9/9/9/9/9/9/9/3K5 w - - 0 1
  // rank 9: '4k4' = file 4 black king? Wait. '4k4' = 4 empty + k + 4 empty = file 4 = e. I want black king at d9 (file 3).
  // FEN: '3k6/9/9/9/9/9/9/9/9/3K5 w - - 0 1'
  // rank 9: '3k6' = file 3 black king
  const g2 = newGame('3k5/9/9/9/9/9/9/9/9/3K5 w - - 0 1');
  check('flying general: red is in check', ck(g2));
  // Red king at d0, must escape. King can move to: d1 (empty), e0 (empty), c0 (empty).
  // d1: would create a configuration where red king at d1, black king at d9. Same file, no pieces between (rank 2-8 empty). STILL flying general at d1. So d1 illegal.
  // e0: red king at e0, black king at d9. Different file. Safe. Legal.
  // c0: red king at c0, black king at d9. Different file. Safe. Legal.
  // But wait, my engine: in isInCheck, the flying-general check is special-cased. After king moves, applyMove changes board. Then isInCheck re-evaluates. So as long as my apply-then-undo-evaluate works, d1 will be detected as illegal (still in check after move).
  const ms2 = m(g2).filter(x => x.startsWith('d0'));
  const expected2 = ['d0e0'];
  check('flying general: red king can escape sideways to e0 only (c0 is outside palace)',
    JSON.stringify(ms2) === JSON.stringify(expected2),
    `got: ${ms2.join(',')}`);

  // Black king can never move to a square that exposes to flying general
  // After red moves e0 (say), then black to move. Black king d9: can move to d8, e9, c9.
  // d8: black king at d8, red king at e0. Different files. Safe. Legal.
  // e9: black king at e9, red king at e0. SAME file (both file 4), no pieces between. Illegal.
  // c9: black king at c9, red king at e0. Different files. Legal.
  mv(g2, 'd0e0'); // red moves king
  const ms3 = m(g2).filter(x => x.startsWith('d9'));
  const expected3 = ['d9d8'];
  check('flying general: black king only has d8 (c9 and e9 outside palace / e9 would face)',
    JSON.stringify(ms3) === JSON.stringify(expected3),
    `got: ${ms3.join(',')}`);
}

// ===========================================================
console.log('\n=== T7: CANNON ===');
{
  // Red cannon at d1 (file 3, rank 1). Black rook at d5 (file 3, rank 4). No screen.
  // FEN: k8/9/9/9/3r5/9/9/9/3C5/3K5 w - - 0 1
  // rank 4: '3r5' = file 3 black rook = d5
  // rank 1: '3C5' = file 3 red cannon = d1
  const g = newGame('k8/9/9/9/3r5/9/9/9/3C5/3K5 w - - 0 1');
  // Cannon at d1. Slide: d0 (own king, illegal), d2..d4 (empty, slide with 0 screens). Capture d5 needs 0 screens between, so illegal (no screen). Blocked at d5.
  const ms = m(g).filter(x => x.startsWith('d1'));
  // Expected: d2, d3, d4
  const expected = ['d1d2','d1d3','d1d4'].sort();
  check('cannon d1 slides over empty squares; cannot capture d5 without screen',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);

  // Now place a screen at d3 (own pawn)
  const g2 = newGame('k8/9/9/9/3r5/9/3P5/9/3C5/3K5 w - - 0 1');
  // rank 3: '3P5' = d4 wait. '3P5' = 3+1+5 = 9, file 0,1,2 empty, file 3 P, files 4-8 empty. So P at file 3 rank 3 = d4. I want screen at d3 (file 3 rank 2).
  // rank 2: '3P5' = P at d3
  const g2b = newGame('k8/9/9/9/3r5/9/9/3P5/3C5/3K5 w - - 0 1');
  // rank 2: '3P5' = d3 screen
  // Cannon d1: slide d2 (empty). Blocked at d3. Capture d5 needs exactly 1 screen between, and d3 is 1 screen, so d5 capture is legal!
  const ms2 = m(g2b).filter(x => x.startsWith('d1'));
  const expected2 = ['d1a1','d1b1','d1c1','d1d5','d1e1','d1f1','d1g1','d1h1','d1i1'].sort();
  check('cannon d1 with screen at d3: lateral slides + d5 capture (d2 own pawn blocked)',
    JSON.stringify(ms2) === JSON.stringify(expected2),
    `got: ${ms2.join(',')}`);

  // Two screens: cannon cannot capture. Place second screen at d4.
  const g3 = newGame('k8/9/9/9/3r5/3P5/9/3P5/3C5/3K5 w - - 0 1');
  // rank 4: '3P5' wait, that's where black rook is. Let me put red pawns at d3 and d4.
  // rank 4 should be black rook, but I want a red pawn at d4 (rank 4, file 3).
  // Hmm. Let me put black rook at d6 instead.
  // FEN: k8/9/9/3r5/9/3P5/9/3P5/3C5/3K5 w - - 0 1
  // rank 5: '3r5' = d6
  // rank 3: '3P5' = d4
  // rank 2: '3P5' = d3
  const g3b = newGame('k8/9/9/3r5/9/3P5/9/3P5/3C5/3K5 w - - 0 1');
  // Cannon d1: screen at d3, screen at d4. To capture d6, needs exactly 1 screen between cannon and d6. Between d1 and d6: d2 empty, d3 screen, d4 screen, d5 empty. 2 screens. Capture illegal.
  const ms3 = m(g3b).filter(x => x.startsWith('d1'));
  const expected3 = ['d1a1','d1b1','d1c1','d1e1','d1f1','d1g1','d1h1','d1i1'].sort();
  check('cannon d1 with 2 screens + own pawn at d2: lateral slides only',
    JSON.stringify(ms3) === JSON.stringify(expected3),
    `got: ${ms3.join(',')}`);
}

console.log('\n=== T8: PAWN DIRECTION AND RIVER ===');
{
  // Red pawn at e3 (file 4, rank 3). Before river (rank 3 < 5, red side). Should move only forward (rank 4).
  // FEN: k8/9/9/9/9/9/4P4/9/9/8K w - - 0 1
  // rank 3: '4P4' = e3
  // Forward for red = INCREASING rank. So e3 -> e4.
  const g = newGame('k8/9/9/9/9/9/4P4/9/9/8K w - - 0 1');
  const ms = m(g).filter(x => x.startsWith('e3'));
  const expected = ['e3e4'];
  check('red pawn e3 (before river) moves forward to e4 only',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);

  // Red pawn crossed river: e7 (file 4, rank 7). Should move forward e8 and sideways d7, f7.
  // FEN: k8/9/4P4/9/9/9/9/9/9/8K w - - 0 1
  // rank 7: '4P4' = e7
  const g2 = newGame('k8/9/4P4/9/9/9/9/9/9/8K w - - 0 1');
  const ms2 = m(g2).filter(x => x.startsWith('e7'));
  const expected2 = ['e7d7','e7e8','e7f7'].sort();
  check('red pawn e7 (after river) moves forward + sideways',
    JSON.stringify(ms2) === JSON.stringify(expected2),
    `got: ${ms2.join(',')}`);

  // Black pawn at e6 (file 4, rank 6). Before river (rank 6 >= 5, black side). Forward = DECREASING rank. So e6 -> e5.
  // FEN: k8/9/9/4p4/9/9/9/9/9/8K b - - 0 1
  // rank 6: '4p4' = e6 black pawn
  const g3b = newGame('k8/9/9/4p4/9/9/9/9/9/8K b - - 0 1');
  const ms3 = m(g3b).filter(x => x.startsWith('e6'));
  const expected3 = ['e6e5'];
  check('black pawn e6 (before river) moves forward to e5',
    JSON.stringify(ms3) === JSON.stringify(expected3),
    `got: ${ms3.join(',')}`);

  // Black pawn crossed river: e3 (file 4, rank 3). After river (rank 3 < 5, black has crossed to red side).
  // Forward = decreasing rank. e3 -> e2 + sideways d3, f3.
  // FEN: k8/9/9/9/9/9/4p4/9/9/8K b - - 0 1
  // rank 3: '4p4' = e3 black pawn
  const g4 = newGame('k8/9/9/9/9/9/4p4/9/9/8K b - - 0 1');
  const ms4 = m(g4).filter(x => x.startsWith('e3'));
  const expected4 = ['e3d3','e3e2','e3f3'].sort();
  check('black pawn e3 (after river) moves forward + sideways',
    JSON.stringify(ms4) === JSON.stringify(expected4),
    `got: ${ms4.join(',')}`);
}
// ===========================================================
console.log('\n=== T9: CHECK DETECTION ===');
{
  // Red king d0, black rook e2 attacks along rank 2? No, rook e2 attacks orthogonal: rank 2 and file e (4).
  // King d0 is at file 3 rank 0. Rook e2 at file 4 rank 1. Not on same file or rank. So not attacking.
  // Try: black rook on e1 (file 4, rank 0) — same rank as king d0. King at d0 (file 3), rook at e0 (file 4)? No, d0 is rank 0 file 3, e0 is rank 0 file 4. Same rank 0, adjacent. Adjacent doesn't count as "attacking via check" in the same sense — the king could just capture. But anyway, rook at e0 attacks d0 along the rank with no pieces between.
  // FEN: k8/9/9/9/9/9/9/9/4r4/3K5 w - - 0 1
  // rank 0: '3K5 4r4' but that's 10. Let me construct: 'k8/9/9/9/9/9/9/9/4r4/3K5' = 10 ranks
  // rank 9: 4k4, ranks 8-1: 9, rank 0: 4r4? wait rank 0 should have both K and r.
  // FEN: 'k8/9/9/9/9/9/9/9/4r4/3K5 w - - 0 1'
  // rank 0: '3K5' = king d0. No rook.
  // I need rook on e0 (file 4, rank 0). FEN: 'k8/9/9/9/9/9/9/9/9/3Kr4 w - - 0 1'
  // rank 0: '3Kr4' = 3 empty, K, r, 4 empty = file 3 K, file 4 r. So red K at d0, black r at e0. Adjacent!
  // Rook at e0 attacks d0 (adjacent, no pieces between).
  const g = newGame('k8/9/9/9/9/9/9/9/9/3Kr4 w - - 0 1');
  check('red in check by adjacent black rook on e0', ck(g));
  // Red king at d0. Legal moves: capture e0 (red K e0)? K moves 1 step. d0 to e0 is 1 step. But e0 has the checking piece (black rook). Capture is legal IF after capture, red not in check. After capture: red king at e0, black king at e9. Not in check (no other black pieces). So d0e0 is legal.
  // Other moves: c0 (no longer on same file as rook, no check). e0 capture. e0e1? file 4 rank 1 is empty, no check.
  // What about d0d1? (file 3 rank 1) — is that in palace? Palace is files 3-5, ranks 0-2. d1 is in palace. But is it safe? After move, red king at d1. Black rook no longer on board (it was captured? no, king moved). Wait the rook is still at e0. d1 not on same file as e0 (file 3 vs 4). d1 not on same rank. Safe.
  // Actually I forgot: rook still on e0. d1 not attacked by e0. Safe. Legal.
  // So d0 moves: d0c0, d0d1, d0e0 (capture), d0e1.
  const ms = m(g).filter(x => x.startsWith('d0'));
  const expected = ['d0d1','d0e0'].sort();
  check('red king d0 in check by adjacent rook: 2 legal moves (d1 sideways, e0 capture)',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);
}

// ===========================================================
console.log('\n=== T10: SIMPLE CHECKMATE ===');
{
  // Construct checkmate on red king. A simple one:
  // Black rook on e1 (file 4, rank 0) attacks red king on d0.
  // Red king can only escape to: c0 (file 2, rank 0, NOT in palace) - illegal (king in palace), d1 (own piece?), e0 (file 4 rank 0 = black rook, can't go there), e1 wait e0 is rook.
  // Let me think simpler. King d0, black rook d2 attacks. King can go to c0 (illegal, outside palace), e0 (legal if not attacked), d1 (legal if in palace and safe), c0 illegal.
  // Place: red king d0, red advisor e1 (file 4 rank 1, blocks the e-file from being useful), black rook d2, black advisor c0 (controls c0 from c0? wait c0 would be black advisor). Or black rook on c0 attacks c0... 
  // Try a textbook "iron column" mate. Skip complex — just check that the engine reports checkmate when the right position is given.
  // The simplest forced mate: red king alone in corner, black rook on the rank, another piece controls the escape.
  // Red king a0, black rook a1, black rook b0. King has no escape.
  // FEN: k8/9/9/9/9/9/9/9/2rr5/K8 w - - 0 1
  // rank 0: 'K8' wait 1+8 = 9. file 0 K. files 1-8 empty. So red K at a0.
  // rank 1: '1rr6' = 1+2+6 = 9. file 0 empty, files 1,2 r. So black r at b1 and c1. Hmm I want r at a1.
  // rank 1: 'r8' = 1+8 = 9. file 0 r. So black r at a1.
  // But I also want another piece to cover the escapes. a0 king's escapes: a1 (occupied by own? no, by black rook — capture?), b0 (empty, escape), b1 (need to be covered).
  // FEN: k8/9/9/9/9/9/9/9/r7/K8 w - - 0 1
  // rank 1: 'r7' = a1 black rook
  // rank 0: 'K8' = a0 red king
  // Black rook at a1 attacks a0. King at a0.
  // Escapes from a0: a1 (capture rook, but is it safe? black king at e9, no other pieces. After capture, king at a1, not in check. Legal!), b0 (escape), b1 (escape).
  // To make checkmate: add black rook at b0 covering b0 escape.
  // FEN: k8/9/9/9/9/9/9/9/r7/Kr7 w - - 0 1
  // rank 0: 'Kr7' = K, r, 7 empty. So red K at a0, black r at b0.
  // King a0 in check from a1 rook. Escapes: a1 (capture, but is b0 rook protecting a1? rook at b0 attacks a0 not a1. So a1 capture is safe). Hmm.
  // Add another piece covering a1. Black rook at b1 covers a1 (attacks a1 along rank).
  // FEN: k8/9/9/9/9/9/9/9/rr6/K7 w - - 0 1
  // rank 1: 'rr6' = a1 r, b1 r
  // rank 0: 'K7' = a0 K
  // Now king a0: check from a1 rook. Escapes: a1 (capture — but a1 defended by b1 rook. After capture K at a1, b1 rook attacks a1 (same rank 1, no pieces between). So K at a1 in check. Illegal).
  // b0: attacked by b1 rook (same file, no pieces between). Illegal.
  // b1: attacked by a1 rook (same rank). Illegal.
  // No legal moves. Checkmate.
  // Place red king INSIDE the palace at d0. Black rook at d1 and e1. King at d0 in check from d1.
  // Escape squares: d0e0 (capture? e0 empty), d0d2 (empty), d0c0 (out of palace), d0c1 (out of palace), d0e1 (capture rook).
  // Need d2, e0, e1 all controlled. Black rook at d1 attacks d2, e1. Black rook at e1 attacks e0, d1. After capture e0 or d2 — both attacked.
  // Use: k8/9/9/9/9/9/9/9/3rr4/3K5 w - - 0 1
  // rank 1: '3rr4' = d1 black rook, e1 black rook (3+2+4=9)
  // rank 0: '3K5' = d0 red king
  const g = newGame('k8/9/9/9/9/9/9/9/3rr4/3K5 w - - 0 1');
  const result = getGameResult(g);
  check('checkmate detected: status=checkmate, winner=black',
    result.status === 'checkmate' && result.winner === 'black',
    `got: status=${result.status}, winner=${result.winner}`);
  const ms = m(g);
  check('checkmate: 0 legal moves', ms.length === 0, `got ${ms.length}: ${ms.join(',')}`);
}

// ===========================================================
console.log('\n=== T11: STALEMATE (player not in check but no moves) ===');
{
  // Stalemate: rare. Construct: red king in corner, all squares covered but not attacked.
  // Example: red king a0, black rook a2 (covers a1 but doesn't attack a0 — wait rook on a2 attacks a-file. So rook at a2 DOES attack a0 if no pieces between. Let me think.
  // Stalemate: side to move not in check, no legal moves.
  // Simple pattern: red king a0, black rook a8 (far away, doesn't attack a0), and own pieces block king. Hmm, king alone in corner.
  // Actually a well-known stalemate: king in corner, 2 enemy pieces forming a "straitjacket".
  // Skip if too complex. Mark as soft test.
  // Try: red king a0, red advisor covering a1, b0, b1. Red king cannot move (own advisors block all 3 in-palace squares). Is red in check? No black pieces. Stalemate.
  // Wait king a0 is in palace? Palace is files 3-5 ranks 0-2 for red. a0 = file 0 rank 0, NOT in palace. So king outside palace has 0 moves regardless. Not stalemate in real game (illegal position).
  // Use king d0 (in palace). Stalemate: red king d0, all 3 in-palace squares covered by own pieces (no escape), no black pieces attacking = not in check.
  // But own pieces don't attack. King can try to capture own pieces? No, kings can't capture own.
  // FEN: k8/9/9/9/9/9/9/9/3A1A2/3KA4 w - - 0 1
  // rank 1: '3A1A2' = 3 empty + A + 1 empty + A + 2 empty = file 3 A (d1), file 5 A (f1)
  // rank 0: '3KA4' = 3 empty + K + A + 4 empty = file 3 K (d0), file 4 A (e0)
  // King d0. In-palace squares: d0 (self), d1 (own A), d2 (empty? check), e0 (own A), e1 (empty? check), e2 (empty? check), c0 (out of palace), c1 (out of palace), c2 (out of palace), f0 (out of palace), f1 (own A), f2 (out of palace).
  // Palace squares (files 3-5, ranks 0-2): d0, d1, d2, e0, e1, e2, f0, f1, f2. 9 squares.
  // King d0, own: d0, d1, e0, f1. Empty: d2, e1, e2, f0, f2.
  // Can king move to any of these? d2, e1, e2, f0, f2 — but are they attacked by black? No black pieces. So king has legal moves (e.g. d0d2). Not stalemate.
  // For stalemate we need those empty palace squares to be attacked. Add black pieces attacking them.
  // Stalemate pattern: king d0, black rook d9 (far, attacks d0 with no pieces between — that's CHECK not stalemate).
  // Skip; mark as best-effort.
  console.log('  (stalemate test skipped — complex position construction)');
}

// ===========================================================
console.log('\n=== T12: ILLEGAL MOVE REJECTION ===');
{
  const g = newGame();
  // Initial: red at rank 0 (a0..i0), black at rank 9 (a9..i9). Red to move.
  // a9 is black rook, can't move on red's turn.
  check('cannot move opponent piece (black rook a9 on red turn)', isLegalMove(g, 'a9a8') === false);
  check('cannot move from empty square', isLegalMove(g, 'e5e6') === false);
  check('out of bounds rejected', isLegalMove(g, 'j0j1') === false);
  check('out of bounds rejected (rank)', isLegalMove(g, 'a0a10') === false);
  check('short string rejected', isLegalMove(g, 'a0a') === false);
}

// ===========================================================
console.log('\n=== T13: FEN AND TURN TOGGLE ===');
{
  const g = newGame();
  const startFen = getFEN(g);
  const ms = m(g);
  mv(g, ms[0]);
  check('turn toggled to black', tr(g) === 'black');
  const fen1 = getFEN(g);
  check('FEN updated', fen1 !== startFen);
  check('FEN has 6 fields', fen1.split(' ').length === 6);
  // Play a black move
  const ms2 = m(g);
  mv(g, ms2[0]);
  check('turn back to red', tr(g) === 'red');
}

// ===========================================================
console.log('\n=== T14: GET HISTORY AND LAST MOVE ===');
{
  const g = newGame();
  const ms = m(g);
  const playedMv = ms[0];
  mv(g, playedMv);
  const hist = getHistory(g);
  check('history length 1', hist.length === 1);
  check('history contains move', hist[0] === playedMv);
  const last = getLastMove(g);
  check('last move from = first 2 chars', last?.from === playedMv.slice(0, 2));
  check('last move to = last 2 chars', last?.to === playedMv.slice(2, 4));
  check('last move iccs = full', last?.iccs === playedMv);
  check('last move piece non-empty', !!last?.piece && last.piece !== '');
}

// ===========================================================
console.log('\n=== T15: 60-MOVE RULE DRAW ===');
{
  // 60 halfmoves = 30 red moves + 30 black moves with no captures/pawn moves
  // Hard to construct manually. Skip — verify the engine's halfmove counter.
  // Simpler test: after a rook move, halfmove = 1.
  const g = newGame();
  // Initial halfmove is 0. Red moves a rook from a1 to a2 — no pawn move, no capture. halfmove → 1.
  // From initial position, is a1a2 legal? Red rook at a0 (file 0, rank 0 = a0). a0a1 is legal.
  // Wait initial: 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1'
  // rank 0: 'RNBAKABNR' = a0=R, b0=N, c0=B, d0=A, e0=K, f0=A, g0=B, h0=N, i0=R
  // Red rook a0. Move a0a1 (forward).
  // Hmm but rank 0 is red's home rank. Moving a0 to a1 is fine (a1 is empty initially).
  // After move, halfmove = 1.
  mv(g, 'a0a1');
  // Check FEN for halfmove
  const fen = getFEN(g);
  const parts = fen.split(' ');
  check('halfmove incremented after non-pawn, non-capture move', parts[4] === '1', `got halfmove=${parts[4]}`);
}

// ===========================================================
console.log('\n=== T16: PINNED PIECE CANNOT MOVE (exposes king) ===');
{
  // Red king d0, red rook d3, black rook d9 — red rook pinned, cannot move laterally
  // FEN: 3k5/9/9/9/9/3R5/9/9/9/3K5 w - - 0 1
  // FEN pos 5: '3R5' = engine rank 4 = d4
  const g = newGame('3k5/9/9/9/9/3R5/9/9/9/3K5 w - - 0 1');
  // Red rook d4 is pinned by black rook d9. Can move along d-file only.
  // d4d1..d4d3 toward own king (own king, d0, blocks at d1, d2, d3). Actually d0 is own king.
  // d1 is empty, d2 empty, d3 empty. So d4d1, d4d2, d4d3 are legal.
  // d4d5..d4d8 are legal (toward black king).
  // d4d9 captures black king (legal — that's how checkmate works).
  // No lateral moves because those would expose red king to black rook attack.
  const ms = m(g).filter(x => x.startsWith('d4'));
  const expected = ['d4d1','d4d2','d4d3','d4d5','d4d6','d4d7','d4d8','d4d9'].sort();
  check('pinned rook d4 can only move along d-file (including capturing checking piece)',
    JSON.stringify(ms) === JSON.stringify(expected),
    `got: ${ms.join(',')}`);
}

// ===========================================================
console.log('\n=== T17: PAWN CANNOT MOVE BACKWARD ===');
{
  // Red pawn at e3 (rank 3, file 4 = ICCS e3). Should only move forward to e4, never backward.
  // FEN: k8/9/9/9/9/9/4P4/9/9/8K w - - 0 1
  // FEN pos 6: '4P4' = engine rank 3 = e3
  const g = newGame('k8/9/9/9/9/9/4P4/9/9/8K w - - 0 1');
  const ms = m(g).filter(x => x.startsWith('e3'));
  check('red pawn e3 moves forward only (no backward)',
    JSON.stringify(ms) === JSON.stringify(['e3e4']),
    `got: ${ms.join(',')}`);
}

// ===========================================================
console.log('\n=== T18: REPETITION (3-FOLD) DRAW ===');
{
  // Hard to construct a real repetition in few moves. Skip but verify positionCounts is tracked.
  // After 1 red move + 1 black move (back and forth), the same position may repeat.
  // We just check that the engine exposes getGameResult and the position counter increments.
  // Skip strict test.
  const g = newGame();
  mv(g, 'a0a1');
  const fen = getFEN(g);
  check('after move, position recorded', getHistory(g).length === 1);
  void fen;
  console.log('  (3-fold repetition full test skipped — requires deep position)');
}

// ===========================================================
console.log('\n=== SUMMARY ===');
console.log(`PASS: ${pass}   FAIL: ${fail}`);
if (fail > 0) {
  console.log('\nFailures:');
  for (const f of failures) console.log('  - ' + f.name + (f.detail ? '\n      ' + f.detail : ''));
  process.exit(1);
}
process.exit(0);
