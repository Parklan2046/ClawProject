import { GameState, Move } from './types';

// Minimal Xiangqi engine implementation
// Full implementation would require complete rule checking

const INITIAL_FEN = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1';

interface EngineState {
  board: string[][];
  turn: 'w' | 'b';
  moveCount: number;
  history: string[];
}

let currentState: EngineState | null = null;

function parseFEN(fen: string): EngineState {
  const [boardPart, turn] = fen.split(' ');
  const ranks = boardPart.split('/');
  const board: string[][] = [];

  for (const rankStr of ranks) {
    const rank: string[] = [];
    for (const char of rankStr) {
      if (/\d/.test(char)) {
        for (let i = 0; i < parseInt(char, 10); i++) {
          rank.push('');
        }
      } else {
        rank.push(char);
      }
    }
    board.push(rank);
  }

  return {
    board,
    turn: turn as 'w' | 'b',
    moveCount: 0,
    history: [],
  };
}

function boardToFEN(state: EngineState): string {
  const ranks: string[] = [];
  for (const rank of state.board) {
    let rankStr = '';
    let emptyCount = 0;
    for (const sq of rank) {
      if (sq === '') {
        emptyCount++;
      } else {
        if (emptyCount > 0) {
          rankStr += emptyCount;
          emptyCount = 0;
        }
        rankStr += sq;
      }
    }
    if (emptyCount > 0) {
      rankStr += emptyCount;
    }
    ranks.push(rankStr);
  }
  return `${ranks.join('/')} ${state.turn} - - 0 ${state.moveCount}`;
}

function getASCII(state: EngineState): string {
  let result = '  +---------------------------+\n';
  for (let r = 0; r < 10; r++) {
    result += `${9 - r} | `;
    for (let f = 0; f < 9; f++) {
      result += (state.board[r][f] || '.') + ' ';
    }
    result += '|\n';
  }
  result += '  +---------------------------+\n';
  result += '    a b c d e f g h i\n';
  return result;
}

// Simplified legal moves generation
function generateLegalMoves(state: EngineState): string[] {
  const moves: string[] = [];
  const isRed = state.turn === 'w';

  for (let r = 0; r < 10; r++) {
    for (let f = 0; f < 9; f++) {
      const piece = state.board[r][f];
      if (!piece) continue;
      const pieceIsRed = piece === piece.toUpperCase();
      if (pieceIsRed !== isRed) continue;

      // Generate moves based on piece type
      const pieceType = piece.toLowerCase();
      switch (pieceType) {
        case 'r': // Rook
          for (let i = r + 1; i < 10 && !state.board[i][f]; i++) moves.push(`${String.fromCharCode(97 + f)}${r}${String.fromCharCode(97 + f)}${i}`);
          for (let i = r - 1; i >= 0 && !state.board[i][f]; i--) moves.push(`${String.fromCharCode(97 + f)}${r}${String.fromCharCode(97 + f)}${i}`);
          for (let i = f + 1; i < 9 && !state.board[r][i]; i++) moves.push(`${String.fromCharCode(97 + f)}${r}${String.fromCharCode(97 + i)}${r}`);
          for (let i = f - 1; i >= 0 && !state.board[r][i]; i--) moves.push(`${String.fromCharCode(97 + f)}${r}${String.fromCharCode(97 + i)}${r}`);
          break;
        case 'p': // Pawn
          const direction = isRed ? -1 : 1;
          const newR = r + direction;
          if (newR >= 0 && newR < 10) {
            moves.push(`${String.fromCharCode(97 + f)}${r}${String.fromCharCode(97 + f)}${newR}`);
          }
          // After crossing river, can move sideways
          const riverCrossed = isRed ? r <= 4 : r >= 5;
          if (riverCrossed) {
            if (f > 0) moves.push(`${String.fromCharCode(97 + f)}${r}${String.fromCharCode(97 + f - 1)}${r}`);
            if (f < 8) moves.push(`${String.fromCharCode(97 + f)}${r}${String.fromCharCode(97 + f + 1)}${r}`);
          }
          break;
        default:
          // For other pieces, generate some plausible moves for demo
          const directions = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
          for (const [dr, df] of directions) {
            const nr = r + dr;
            const nf = f + df;
            if (nr >= 0 && nr < 10 && nf >= 0 && nf < 9) {
              moves.push(`${String.fromCharCode(97 + f)}${r}${String.fromCharCode(97 + nf)}${nr}`);
            }
          }
      }
    }
  }

  return moves;
}

function iccsToCoords(iccs: string): { from: [number, number]; to: [number, number] } {
  const fromFile = iccs.charCodeAt(0) - 97;
  const fromRank = parseInt(iccs[1], 10);
  const toFile = iccs.charCodeAt(2) - 97;
  const toRank = parseInt(iccs[3], 10);
  return {
    from: [fromRank, fromFile],
    to: [toRank, toFile],
  };
}

export async function initEngine() {
  currentState = parseFEN(INITIAL_FEN);
}

export function createGame(fen?: string): any {
  currentState = parseFEN(fen || INITIAL_FEN);
  return {
    _state: currentState,
  };
}

export function getFEN(game: any): string {
  return boardToFEN(game._state);
}

export function getASCII(game: any): string {
  return getASCII(game._state);
}

export function getLegalMoves(game: any): string[] {
  return generateLegalMoves(game._state);
}

export function makeMove(game: any, iccs: string): boolean {
  const state = game._state;
  const { from, to } = iccsToCoords(iccs);

  if (from[0] < 0 || from[0] >= 10 || from[1] < 0 || from[1] >= 9) return false;
  if (to[0] < 0 || to[0] >= 10 || to[1] < 0 || to[1] >= 9) return false;

  const piece = state.board[from[0]][from[1]];
  if (!piece) return false;

  const pieceIsRed = piece === piece.toUpperCase();
  const isRedTurn = state.turn === 'w';
  if (pieceIsRed !== isRedTurn) return false;

  // Make the move
  state.board[to[0]][to[1]] = piece;
  state.board[from[0]][from[1]] = '';
  state.turn = state.turn === 'w' ? 'b' : 'w';
  state.moveCount++;
  state.history.push(iccs);

  return true;
}

export function getGameStatus(game: any): GameState['status'] {
  // Simplified - just check if game is ongoing
  return 'playing';
}

export function getTurn(game: any): 'red' | 'black' {
  return game._state.turn === 'w' ? 'red' : 'black';
}

export function getHistory(game: any): string[] {
  return game._state.history;
}

export function resetGame(game: any): void {
  game._state = parseFEN(INITIAL_FEN);
}

export function getMoveHistory(game: any): Move[] {
  return game._state.history.map((iccs: string) => ({
    from: iccs.slice(0, 2),
    to: iccs.slice(2, 4),
    iccs,
    piece: '',
  }));
}

export function getLastMove(game: any): Move | null {
  const hist = game._state.history;
  if (!hist.length) return null;
  const iccs = hist[hist.length - 1];
  return {
    from: iccs.slice(0, 2),
    to: iccs.slice(2, 4),
    iccs,
    piece: '',
  };
}
