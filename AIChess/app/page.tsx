'use client';

import { useEffect, useState, useCallback } from 'react';
import { Scene } from '@/components/3d/Scene';
import { GameControls } from '@/components/GameControls';
import { MoveHistory } from '@/components/MoveHistory';
import { useGame } from '@/hooks/useGame';
import { GameConfig } from '@/lib/types';
import { Trophy, Swords, AlertCircle, X } from 'lucide-react';

export default function Home() {
  const { init, state, requestLLMMove, config, errorMessage, clearError } = useGame();
  const [gameStarted, setGameStarted] = useState(false);

  useEffect(() => {
    init();
  }, [init]);

  const handleStartGame = useCallback((gameConfig: GameConfig) => {
    setGameStarted(true);
  }, []);

  useEffect(() => {
    if (!gameStarted || !config || state.status !== 'playing') return;

    const currentTurn = state.turn;
    const player = currentTurn === 'red' ? config.redPlayer : config.blackPlayer;

    if (player.type === 'llm') {
      const timer = setTimeout(() => {
        requestLLMMove();
      }, config.delayBetweenMoves);
      return () => clearTimeout(timer);
    }
  }, [gameStarted, config, state.turn, state.status, requestLLMMove]);

  const winnerText = state.winner === 'red' ? '紅方勝利' : state.winner === 'black' ? '黑方勝利' : '和棋';
  const statusText =
    state.status === 'checkmate' ? '將死' : state.status === 'stalemate' ? '困斃（和棋）' : state.status === 'draw' ? '和棋' : '';

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-red-600 to-amber-500 flex items-center justify-center text-2xl">
              ♟
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-400 bg-clip-text text-transparent">
                象棋 LLM 競技場
              </h1>
              <p className="text-xs text-gray-500">3D 中國象棋 · AI 對決 · 完整規則</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {state.status !== 'playing' && gameStarted && (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/30">
                <Trophy className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">
                  {winnerText} · {statusText}
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {errorMessage && (
        <div className="max-w-7xl mx-auto px-4 mt-3">
          <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-300">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {errorMessage}
            </div>
            <button onClick={clearError} className="text-red-300 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden" style={{ height: '600px' }}>
              <Scene />
            </div>
            <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-red-500" /> 紅方
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-gray-700 border border-gray-500" /> 黑方
                </span>
              </div>
              <div>
                總步數: <span className="text-amber-400 font-mono">{state.history.length}</span>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <GameControls onStartGame={handleStartGame} />
            <MoveHistory />
          </div>
        </div>
      </div>

      <footer className="border-t border-gray-800 mt-12 py-6 text-center text-sm text-gray-600">
        <p>象棋 LLM 競技場 · 完整 7 兵種規則 · 飛將 / 將死 / 困斃 / 三次重複 / 60 回合和棋</p>
      </footer>
    </main>
  );
}
