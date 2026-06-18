export interface GameState { fen: string; ascii: string; turn: 'red' | 'black'; history: string[]; status: 'playing' | 'checkmate' | 'stalemate' | 'draw'; winner: 'red' | 'black' | null; }
export interface Move { from: string; to: string; iccs: string; piece: string; captured?: string; san?: string; }

export const INITIAL_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1';

export type Color = 'w' | 'b';
export type PieceChar = 'k' | 'a' | 'b' | 'n' | 'r' | 'c' | 'p';

export interface EngineState {
  board: string[][];
  turn: Color;
  halfmove: number;
  fullmove: number;
  history: string[];
  positionCounts: Map<string, number>;
}

let currentState: EngineState | null = null;

export function isRedPiece(p: string): boolean {
  return p >= 'A' && p <= 'Z';
}

export function isBlackPiece(p: string): boolean {
  return p >= 'a' && p <= 'z';
}

export function inBounds(r: number, f: number): boolean {
  return r >= 0 && r < 10 && f >= 0 && f < 9;
}

export function inRedPalace(r: number, f: number): boolean {
  return r >= 0 && r <= 2 && f >= 3 && f <= 5;
}

export function inBlackPalace(r: number, f: number): boolean {
  return r >= 7 && r <= 9 && f >= 3 && f <= 5;
}

export function inOwnHalf(r: number, isRed: boolean): boolean {
  return isRed ? r <= 4 : r >= 5;
}

export function findKing(board: string[][], isRed: boolean): [number, number] | null {
  const target = isRed ? 'K' : 'k';
  for (let r = 0; r < 10; r++) {
    for (let f = 0; f < 9; f++) {
      if (board[r][f] === target) return [r, f];
    }
  }
  return null;
}

function parseFEN(fen: string): EngineState {
  const parts = fen.trim().split(/\s+/);
  const boardPart = parts[0];
  const turn = (parts[1] || 'w') as Color;
  const ranks = boardPart.split('/');
  if (ranks.length !== 10) throw new Error(`Invalid FEN: expected 10 ranks, got ${ranks.length}`);

  const board: string[][] = new Array(10);
  for (let i = 0; i < 10; i++) board[i] = new Array(9).fill('');
  for (let r = 0; r < 10; r++) {
    const rankStr = ranks[r];
    const rank: string[] = [];
    for (const ch of rankStr) {
      if (ch >= '0' && ch <= '9') {
        const n = parseInt(ch, 10);
        for (let i = 0; i < n; i++) rank.push('');
      } else if ('RNBAKCP rnba kcp'.includes(ch)) {
        rank.push(ch);
      } else {
        throw new Error(`Invalid FEN character '${ch}'`);
      }
    }
    if (rank.length !== 9) throw new Error(`Invalid FEN rank width: expected 9, got ${rank.length} in '${rankStr}'`);
    board[9 - r] = rank;
  }

  return {
    board,
    turn,
    halfmove: parseInt(parts[4] || '0', 10) || 0,
    fullmove: parseInt(parts[5] || '1', 10) || 1,
    history: [],
    positionCounts: new Map(),
  };
}

function boardToFEN(state: EngineState): string {
  const ranks: string[] = [];
  for (let r = 0; r < 10; r++) {
    let rankStr = '';
    let empty = 0;
    for (let f = 0; f < 9; f++) {
      const sq = state.board[r][f];
      if (sq === '') {
        empty++;
      } else {
        if (empty > 0) {
          rankStr += empty;
          empty = 0;
        }
        rankStr += sq;
      }
    }
    if (empty > 0) rankStr += empty;
    ranks.push(rankStr);
  }
  return `${ranks.join('/')} ${state.turn} - - ${state.halfmove} ${state.fullmove}`;
}

function positionKey(state: EngineState): string {
  return `${boardToFEN(state).split(' ').slice(0, 2).join(' ')}`;
}

function recordPosition(state: EngineState): void {
  const key = positionKey(state);
  state.positionCounts.set(key, (state.positionCounts.get(key) || 0) + 1);
}

function squareAttackedBy(state: EngineState, r: number, f: number, byRed: boolean): boolean {
  const board = state.board;

  for (let rr = 0; rr < 10; rr++) {
    for (let ff = 0; ff < 9; ff++) {
      const p = board[rr][ff];
      if (!p) continue;
      const pIsRed = isRedPiece(p);
      if (pIsRed !== byRed) continue;
      const t = p.toLowerCase();
      const dr = r - rr;
      const df = f - ff;
      const adr = Math.abs(dr);
      const adf = Math.abs(df);

      if (t === 'p') {
        const forward = byRed ? -1 : 1;
        if (dr === forward && df === 0) return true;
        const crossed = byRed ? rr <= 4 : rr >= 5;
        if (crossed && dr === 0 && adf === 1) return true;
      } else if (t === 'n') {
        if ((adr === 1 && adf === 2) || (adr === 2 && adf === 1)) {
          if (adr === 2) {
            const legR = rr + (dr > 0 ? 1 : -1);
            if (board[legR][ff] === '') return true;
          } else {
            const legF = ff + (df > 0 ? 1 : -1);
            if (board[rr][legF] === '') return true;
          }
        }
      } else if (t === 'r' || t === 'c') {
        if (dr === 0 && df !== 0) {
          const step = df > 0 ? 1 : -1;
          let screens = 0;
          for (let i = ff + step; i !== f; i += step) {
            if (board[rr][i] !== '') screens++;
          }
          if (t === 'r') {
            if (screens === 0) return true;
          } else {
            if (screens === 1) return true;
          }
        } else if (df === 0 && dr !== 0) {
          const step = dr > 0 ? 1 : -1;
          let screens = 0;
          for (let i = rr + step; i !== r; i += step) {
            if (board[i][ff] !== '') screens++;
          }
          if (t === 'r') {
            if (screens === 0) return true;
          } else {
            if (screens === 1) return true;
          }
        }
      } else if (t === 'b') {
        if (adr === 2 && adf === 2) {
          const eyeR = rr + dr / 2;
          const eyeF = ff + df / 2;
          if (board[eyeR][eyeF] === '' && inOwnHalf(eyeR, byRed)) return true;
        }
      } else if (t === 'a') {
        if (adr === 1 && adf === 1) {
          if (byRed ? inRedPalace(rr, ff) : inBlackPalace(rr, ff)) return true;
        }
      } else if (t === 'k') {
        if (adr + adf === 1) {
          if (byRed ? inRedPalace(rr, ff) : inBlackPalace(rr, ff)) return true;
        }
      }
    }
  }

  const redKing = findKing(board, true);
  const blackKing = findKing(board, false);
  if (redKing && blackKing && redKing[1] === blackKing[1]) {
    const lo = Math.min(redKing[0], blackKing[0]) + 1;
    const hi = Math.max(redKing[0], blackKing[0]);
    let blocked = false;
    for (let i = lo; i < hi; i++) {
      if (board[i][redKing[1]] !== '') {
        blocked = true;
        break;
      }
    }
    if (!blocked) {
      if (byRed && (r === blackKing[0] && f === blackKing[1])) return true;
      if (!byRed && (r === redKing[0] && f === redKing[1])) return true;
    }
  }

  return false;
}

export function isSquareAttacked(state: EngineState, r: number, f: number, byRed: boolean): boolean {
  return squareAttackedBy(state, r, f, byRed);
}

export function isInCheck(state: EngineState, isRed: boolean): boolean {
  const k = findKing(state.board, isRed);
  if (!k) return false;
  return isSquareAttacked(state, k[0], k[1], !isRed);
}

function pseudoMovesForPiece(state: EngineState, r: number, f: number): string[] {
  const board = state.board;
  const piece = board[r][f];
  if (!piece) return [];
  const isRed = isRedPiece(piece);
  const t = piece.toLowerCase() as PieceChar;
  const moves: string[] = [];

  const tryAdd = (nr: number, nf: number) => {
    if (!inBounds(nr, nf)) return;
    const target = board[nr][nf];
    if (target === '') {
      moves.push(sq(r, f, nr, nf));
    } else if (isRedPiece(target) !== isRed) {
      moves.push(sq(r, f, nr, nf));
    }
  };

  if (t === 'r') {
    for (let i = r + 1; i < 10; i++) {
      if (board[i][f] === '') moves.push(sq(r, f, i, f));
      else {
        if (isRedPiece(board[i][f]) !== isRed) moves.push(sq(r, f, i, f));
        break;
      }
    }
    for (let i = r - 1; i >= 0; i--) {
      if (board[i][f] === '') moves.push(sq(r, f, i, f));
      else {
        if (isRedPiece(board[i][f]) !== isRed) moves.push(sq(r, f, i, f));
        break;
      }
    }
    for (let i = f + 1; i < 9; i++) {
      if (board[r][i] === '') moves.push(sq(r, f, r, i));
      else {
        if (isRedPiece(board[r][i]) !== isRed) moves.push(sq(r, f, r, i));
        break;
      }
    }
    for (let i = f - 1; i >= 0; i--) {
      if (board[r][i] === '') moves.push(sq(r, f, r, i));
      else {
        if (isRedPiece(board[r][i]) !== isRed) moves.push(sq(r, f, r, i));
        break;
      }
    }
  } else if (t === 'c') {
    for (let i = r + 1; i < 10; i++) {
      if (board[i][f] === '') moves.push(sq(r, f, i, f));
      else {
        for (let j = i + 1; j < 10; j++) {
          if (board[j][f] !== '') {
            if (isRedPiece(board[j][f]) !== isRed) moves.push(sq(r, f, j, f));
            break;
          }
        }
        break;
      }
    }
    for (let i = r - 1; i >= 0; i--) {
      if (board[i][f] === '') moves.push(sq(r, f, i, f));
      else {
        for (let j = i - 1; j >= 0; j--) {
          if (board[j][f] !== '') {
            if (isRedPiece(board[j][f]) !== isRed) moves.push(sq(r, f, j, f));
            break;
          }
        }
        break;
      }
    }
    for (let i = f + 1; i < 9; i++) {
      if (board[r][i] === '') moves.push(sq(r, f, r, i));
      else {
        for (let j = i + 1; j < 9; j++) {
          if (board[r][j] !== '') {
            if (isRedPiece(board[r][j]) !== isRed) moves.push(sq(r, f, r, j));
            break;
          }
        }
        break;
      }
    }
    for (let i = f - 1; i >= 0; i--) {
      if (board[r][i] === '') moves.push(sq(r, f, r, i));
      else {
        for (let j = i - 1; j >= 0; j--) {
          if (board[r][j] !== '') {
            if (isRedPiece(board[r][j]) !== isRed) moves.push(sq(r, f, r, j));
            break;
          }
        }
        break;
      }
    }
  } else if (t === 'n') {
    const candidates: Array<[number, number, number, number]> = [
      [r - 2, f - 1, r - 1, f],
      [r - 2, f + 1, r - 1, f],
      [r + 2, f - 1, r + 1, f],
      [r + 2, f + 1, r + 1, f],
      [r - 1, f - 2, r, f - 1],
      [r + 1, f - 2, r, f - 1],
      [r - 1, f + 2, r, f + 1],
      [r + 1, f + 2, r, f + 1],
    ];
    for (const [nr, nf, lr, lf] of candidates) {
      if (!inBounds(nr, nf)) continue;
      if (board[lr][lf] !== '') continue;
      const target = board[nr][nf];
      if (target === '' || isRedPiece(target) !== isRed) moves.push(sq(r, f, nr, nf));
    }
  } else if (t === 'b') {
    const deltas: Array<[number, number]> = [[2, 2], [2, -2], [-2, 2], [-2, -2]];
    for (const [dr, df] of deltas) {
      const nr = r + dr;
      const nf = f + df;
      const eyeR = r + dr / 2;
      const eyeF = f + df / 2;
      if (!inBounds(nr, nf)) continue;
      if (!inOwnHalf(nr, isRed)) continue;
      if (board[eyeR][eyeF] !== '') continue;
      const target = board[nr][nf];
      if (target === '' || isRedPiece(target) !== isRed) moves.push(sq(r, f, nr, nf));
    }
  } else if (t === 'a') {
    const inPalace = isRed ? inRedPalace : inBlackPalace;
    if (!inPalace(r, f)) return moves;
    for (const [dr, df] of [[1, 1], [1, -1], [-1, 1], [-1, -1]] as Array<[number, number]>) {
      const nr = r + dr;
      const nf = f + df;
      if (!inBounds(nr, nf)) continue;
      if (!inPalace(nr, nf)) continue;
      const target = board[nr][nf];
      if (target === '' || isRedPiece(target) !== isRed) moves.push(sq(r, f, nr, nf));
    }
  } else if (t === 'k') {
    const inPalace = isRed ? inRedPalace : inBlackPalace;
    if (!inPalace(r, f)) return moves;
    for (const [dr, df] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as Array<[number, number]>) {
      const nr = r + dr;
      const nf = f + df;
      if (!inBounds(nr, nf)) continue;
      if (!inPalace(nr, nf)) continue;
      const target = board[nr][nf];
      if (target === '' || isRedPiece(target) !== isRed) moves.push(sq(r, f, nr, nf));
    }
  } else if (t === 'p') {
    const forward = isRed ? 1 : -1;
    const nr = r + forward;
    if (inBounds(nr, f)) {
      const target = board[nr][f];
      if (target === '' || isRedPiece(target) !== isRed) moves.push(sq(r, f, nr, f));
    }
    const crossed = isRed ? r >= 5 : r <= 4;
    if (crossed) {
      if (f > 0) {
        const target = board[r][f - 1];
        if (target === '' || isRedPiece(target) !== isRed) moves.push(sq(r, f, r, f - 1));
      }
      if (f < 8) {
        const target = board[r][f + 1];
        if (target === '' || isRedPiece(target) !== isRed) moves.push(sq(r, f, r, f + 1));
      }
    }
  }

  return moves;
}

function sq(r1: number, f1: number, r2: number, f2: number): string {
  return `${String.fromCharCode(97 + f1)}${r1}${String.fromCharCode(97 + f2)}${r2}`;
}

function applyMove(state: EngineState, fromR: number, fromF: number, toR: number, toF: number): void {
  const piece = state.board[fromR][fromF];
  const captured = state.board[toR][toF];
  state.board[toR][toF] = piece;
  state.board[fromR][fromF] = '';
  state.turn = state.turn === 'w' ? 'b' : 'w';
  if (state.turn === 'w') state.fullmove++;
  if (captured !== '' || piece.toLowerCase() === 'p') {
    state.halfmove = 0;
  } else {
    state.halfmove++;
  }
}

function undoMove(state: EngineState, fromR: number, fromF: number, toR: number, toF: number, captured: string, prevTurn: Color, prevHalfmove: number, prevFullmove: number): void {
  const piece = state.board[toR][toF];
  state.board[fromR][fromF] = piece;
  state.board[toR][toF] = captured;
  state.turn = prevTurn;
  state.halfmove = prevHalfmove;
  state.fullmove = prevFullmove;
}

export function generateLegalMoves(state: EngineState): string[] {
  const isRed = state.turn === 'w';
  const moves: string[] = [];
  for (let r = 0; r < 10; r++) {
    for (let f = 0; f < 9; f++) {
      const p = state.board[r][f];
      if (!p) continue;
      if (isRedPiece(p) !== isRed) continue;
      const pms = pseudoMovesForPiece(state, r, f);
      for (const iccs of pms) {
        const fr = parseInt(iccs[1], 10);
        const ff = iccs.charCodeAt(0) - 97;
        const tr = parseInt(iccs[3], 10);
        const tf = iccs.charCodeAt(2) - 97;
        const captured = state.board[tr][tf];
        const prevTurn = state.turn;
        const prevHalf = state.halfmove;
        const prevFull = state.fullmove;
        applyMove(state, fr, ff, tr, tf);
        const inCheck = isInCheck(state, isRed);
        undoMove(state, fr, ff, tr, tf, captured, prevTurn, prevHalf, prevFull);
        if (!inCheck) moves.push(iccs);
      }
    }
  }
  return moves;
}

export function getLegalMoves(game: any): string[] {
  return generateLegalMoves(game._state);
}

export function getLegalMovesFromSquare(state: EngineState, r: number, f: number): string[] {
  return generateLegalMoves(state).filter(m => m[0] === String.fromCharCode(97 + f) && m[1] === String(r));
}

export type GameStatusResult = {
  status: 'playing' | 'checkmate' | 'stalemate' | 'draw';
  winner: 'red' | 'black' | null;
  reason: string;
};

export function evaluateStatus(state: EngineState): GameStatusResult {
  const isRed = state.turn === 'w';
  const moves = generateLegalMoves(state);
  const inCheck = isInCheck(state, isRed);

  if (state.halfmove >= 60) {
    return { status: 'draw', winner: null, reason: '60-move rule' };
  }
  const key = positionKey(state);
  const reps = state.positionCounts.get(key) || 0;
  if (reps >= 3) {
    return { status: 'draw', winner: null, reason: 'threefold repetition' };
  }

  if (moves.length === 0) {
    if (inCheck) {
      return { status: 'checkmate', winner: isRed ? 'black' : 'red', reason: 'checkmate' };
    }
    return { status: 'stalemate', winner: null, reason: 'stalemate' };
  }

  return { status: 'playing', winner: null, reason: 'ongoing' };
}

export async function initEngine(): Promise<void> {
  currentState = parseFEN(INITIAL_FEN);
  recordPosition(currentState);
}

export function createGame(fen?: string): any {
  const state = parseFEN(fen || INITIAL_FEN);
  recordPosition(state);
  return { _state: state };
}

export function getFEN(game: any): string {
  return boardToFEN(game._state);
}

export function getASCII(state: EngineState): string {
  let result = '  +---------------------------+\n';
  for (let r = 0; r < 10; r++) {
    result += `${9 - r} | `;
    for (let f = 0; f < 9; f++) {
      result += ((state.board[r] && state.board[r][f]) || '.') + ' ';
    }
    result += '|\n';
  }
  result += '  +---------------------------+\n';
  result += '    a b c d e f g h i\n';
  return result;
}

export function getASCIIForGame(game: any): string {
  return getASCII(game._state);
}

export function getASCIIFromFEN(fen: string): string {
  return getASCII(parseFEN(fen));
}

export function isLegalMove(game: any, iccs: string): boolean {
  if (iccs.length !== 4) return false;
  const fromF = iccs.charCodeAt(0) - 97;
  const fromR = parseInt(iccs[1], 10);
  const toF = iccs.charCodeAt(2) - 97;
  const toR = parseInt(iccs[3], 10);
  if (!inBounds(fromR, fromF) || !inBounds(toR, toF)) return false;
  const piece = game._state.board[fromR][fromF];
  if (!piece) return false;
  const isRed = isRedPiece(piece);
  if (isRed !== (game._state.turn === 'w')) return false;
  const pms = pseudoMovesForPiece(game._state, fromR, fromF);
  if (!pms.includes(iccs)) return false;
  const captured = game._state.board[toR][toF];
  const prevTurn = game._state.turn;
  const prevHalf = game._state.halfmove;
  const prevFull = game._state.fullmove;
  applyMove(game._state, fromR, fromF, toR, toF);
  const inCheck = isInCheck(game._state, isRed);
  undoMove(game._state, fromR, fromF, toR, toF, captured, prevTurn, prevHalf, prevFull);
  return !inCheck;
}

export function makeMove(game: any, iccs: string): boolean {
  if (!isLegalMove(game, iccs)) return false;
  const fromF = iccs.charCodeAt(0) - 97;
  const fromR = parseInt(iccs[1], 10);
  const toF = iccs.charCodeAt(2) - 97;
  const toR = parseInt(iccs[3], 10);
  const piece = game._state.board[fromR][fromF];
  const captured = game._state.board[toR][toF];
  applyMove(game._state, fromR, fromF, toR, toF);
  recordPosition(game._state);
  game._state.history.push(iccs);
  game._lastMove = {
    from: iccs.slice(0, 2),
    to: iccs.slice(2, 4),
    iccs,
    piece,
    captured: captured || undefined,
  };
  return true;
}

export function getGameStatus(game: any): GameState['status'] {
  return evaluateStatus(game._state).status;
}

export function getGameResult(game: any): GameStatusResult {
  return evaluateStatus(game._state);
}

export function getTurn(game: any): 'red' | 'black' {
  return game._state.turn === 'w' ? 'red' : 'black';
}

export function getHistory(game: any): string[] {
  return game._state.history;
}

export function resetGame(game: any): void {
  const fresh = parseFEN(INITIAL_FEN);
  game._state = fresh;
  recordPosition(game._state);
  game._lastMove = null;
}

export function getMoveHistory(game: any): Move[] {
  return game._state.history.map((iccs: string, i: number) => {
    const fromR = parseInt(iccs[1], 10);
    const fromF = iccs.charCodeAt(0) - 97;
    const toR = parseInt(iccs[3], 10);
    const toF = iccs.charCodeAt(2) - 97;
    const piece = game._state.board[toR][toF] || '';
    return {
      from: iccs.slice(0, 2),
      to: iccs.slice(2, 4),
      iccs,
      piece,
    };
  });
}

export function getLastMove(game: any): Move | null {
  return game._lastMove || null;
}

export function isInCheckPublic(game: any): boolean {
  return isInCheck(game._state, game._state.turn === 'w');
}
