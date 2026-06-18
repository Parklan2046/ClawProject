import { create } from 'zustand';
import { GameState, GameConfig, Move, LLMConfig } from '@/lib/types';
import { initEngine, createGame, getFEN, getASCII, getLegalMoves, makeMove, getGameStatus, getTurn, getHistory, getLastMove, isLegalMove, getGameResult, isInCheckPublic } from '@/lib/xiangqi-engine';
import { LLMPlayer } from '@/lib/llm-player';

interface GameStore {
  game: any;
  state: GameState;
  config: GameConfig | null;
  isThinking: boolean;
  currentLLM: string | null;
  selectedSquare: string | null;
  legalMoves: string[];
  lastMove: Move | null;
  inCheck: 'red' | 'black' | null;
  errorMessage: string | null;
  init: () => Promise<void>;
  newGame: (config: GameConfig) => void;
  makeMove: (iccs: string) => boolean;
  requestLLMMove: () => Promise<void>;
  setSelectedSquare: (sq: string | null) => void;
  getLegalMovesForSquare: (sq: string) => string[];
  clearError: () => void;
}

function snapshot(game: any): GameState {
  const result = getGameResult(game);
  const turn = getTurn(game);
  return {
    fen: getFEN(game),
    ascii: getASCII(game),
    turn,
    history: getHistory(game),
    status: result.status,
    winner: result.winner,
  };
}

export const useGame = create<GameStore>((set, get) => ({
  game: null,
  state: {
    fen: '',
    ascii: '',
    turn: 'red',
    history: [],
    status: 'playing',
    winner: null,
  },
  config: null,
  isThinking: false,
  currentLLM: null,
  selectedSquare: null,
  legalMoves: [],
  lastMove: null,
  inCheck: null,
  errorMessage: null,

  init: async () => {
    await initEngine();
    const game = createGame();
    set({
      game,
      state: snapshot(game),
      legalMoves: getLegalMoves(game),
      lastMove: null,
      selectedSquare: null,
      inCheck: isInCheckPublic(game) ? getTurn(game) : null,
    });
  },

  newGame: (config: GameConfig) => {
    const game = createGame();
    set({
      game,
      config,
      state: snapshot(game),
      lastMove: null,
      selectedSquare: null,
      legalMoves: getLegalMoves(game),
      inCheck: null,
      errorMessage: null,
    });
  },

  makeMove: (iccs: string) => {
    const { game, state } = get();
    if (!game) return false;
    if (state.status !== 'playing') {
      set({ errorMessage: '對局已結束' });
      return false;
    }
    if (!isLegalMove(game, iccs)) {
      set({ errorMessage: `非法棋步: ${iccs}` });
      return false;
    }
    const success = makeMove(game, iccs);
    if (success) {
      const newState = snapshot(game);
      const checkingSide = isInCheckPublic(game) ? newState.turn : null;
      set({
        state: newState,
        lastMove: getLastMove(game),
        selectedSquare: null,
        legalMoves: newState.status === 'playing' ? getLegalMoves(game) : [],
        inCheck: checkingSide,
        errorMessage: null,
      });
    }
    return success;
  },

  requestLLMMove: async () => {
    const { game, config, state } = get();
    if (!game || !config || state.status !== 'playing') return;

    const currentTurn = state.turn;
    const player = currentTurn === 'red' ? config.redPlayer : config.blackPlayer;

    if (player.type !== 'llm' || !player.config) return;

    set({ isThinking: true, currentLLM: player.config.name, errorMessage: null });

    try {
      const llm = new LLMPlayer(player.config);
      const legalMoves = getLegalMoves(game);
      if (legalMoves.length === 0) {
        set({ isThinking: false, currentLLM: null });
        return;
      }
      const response = await llm.getMove(
        getFEN(game),
        getASCII(game),
        legalMoves,
        currentTurn
      );

      if (!get().makeMove(response.move)) {
        if (legalMoves.length > 0) {
          get().makeMove(legalMoves[0]);
        }
      }
    } catch (error) {
      console.error('LLM move failed:', error);
      set({ errorMessage: 'LLM 呼叫失敗，請檢查 API Key 設定' });
    } finally {
      set({ isThinking: false, currentLLM: null });
    }
  },

  setSelectedSquare: (sq: string | null) => {
    set({ selectedSquare: sq });
  },

  getLegalMovesForSquare: (sq: string) => {
    const { legalMoves } = get();
    return legalMoves.filter((m: string) => m.startsWith(sq));
  },

  clearError: () => set({ errorMessage: null }),
}));
