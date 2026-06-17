import { create } from 'zustand';
import { GameState, GameConfig, Move, LLMConfig } from '@/lib/types';
import { initEngine, createGame, getFEN, getASCII, getLegalMoves, makeMove, getGameStatus, getTurn, getHistory, getLastMove } from '@/lib/xiangqi-engine';
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
  init: () => Promise<void>;
  newGame: (config: GameConfig) => void;
  makeMove: (iccs: string) => boolean;
  requestLLMMove: () => Promise<void>;
  setSelectedSquare: (sq: string | null) => void;
  getLegalMovesForSquare: (sq: string) => string[];
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

  init: async () => {
    await initEngine();
    const game = createGame();
    const state = {
      fen: getFEN(game),
      ascii: getASCII(game),
      turn: getTurn(game),
      history: getHistory(game),
      status: getGameStatus(game),
      winner: null,
    };
    set({ game, state, legalMoves: getLegalMoves(game) });
  },

  newGame: (config: GameConfig) => {
    const game = createGame();
    const state = {
      fen: getFEN(game),
      ascii: getASCII(game),
      turn: getTurn(game),
      history: getHistory(game),
      status: getGameStatus(game),
      winner: null,
    };
    set({ game, config, state, lastMove: null, selectedSquare: null, legalMoves: getLegalMoves(game) });
  },

  makeMove: (iccs: string) => {
    const { game } = get();
    if (!game) return false;
    const success = makeMove(game, iccs);
    if (success) {
      const state = {
        fen: getFEN(game),
        ascii: getASCII(game),
        turn: getTurn(game),
        history: getHistory(game),
        status: getGameStatus(game),
        winner: getGameStatus(game) !== 'playing' ? getTurn(game) === 'red' ? 'black' : 'red' : null,
      };
      set({
        state,
        lastMove: getLastMove(game),
        selectedSquare: null,
        legalMoves: getLegalMoves(game),
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

    set({ isThinking: true, currentLLM: player.config.name });

    try {
      const llm = new LLMPlayer(player.config);
      const legalMoves = getLegalMoves(game);
      const response = await llm.getMove(
        getFEN(game),
        getASCII(game),
        legalMoves,
        currentTurn
      );

      get().makeMove(response.move);
    } catch (error) {
      console.error('LLM move failed:', error);
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
}));
