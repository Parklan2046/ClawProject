export interface LLMConfig {
  id: string;
  name: string;
  provider: 'deepseek' | 'minimax' | 'qwen' | 'moonshot' | 'custom';
  baseURL: string;
  apiKey: string;
  model: string;
  temperature: number;
  maxRetries: number;
}

export interface GameState {
  fen: string;
  ascii: string;
  turn: 'red' | 'black';
  history: string[];
  status: 'playing' | 'checkmate' | 'stalemate' | 'draw';
  winner: 'red' | 'black' | null;
}

export interface Move {
  from: string;
  to: string;
  iccs: string;
  piece: string;
  captured?: string;
  san?: string;
}

export interface LLMResponse {
  move: string;
  reasoning: string;
}

export interface Player {
  type: 'human' | 'llm';
  config?: LLMConfig;
  side: 'red' | 'black';
}

export interface GameConfig {
  redPlayer: Player;
  blackPlayer: Player;
  delayBetweenMoves: number;
}
