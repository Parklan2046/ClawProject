'use client';

import { useState } from 'react';
import { useGame } from '@/hooks/useGame';
import { GameConfig, LLMConfig, Player } from '@/lib/types';
import { DEFAULT_LLM_CONFIGS } from '@/lib/constants';
import { Swords, User, Bot, Play, RotateCcw } from 'lucide-react';

interface GameControlsProps {
  onStartGame: (config: GameConfig) => void;
}

export function GameControls({ onStartGame }: GameControlsProps) {
  const { state, config, isThinking, currentLLM, newGame } = useGame();
  const [redType, setRedType] = useState<'human' | 'llm'>('llm');
  const [blackType, setBlackType] = useState<'human' | 'llm'>('llm');
  const [redLLM, setRedLLM] = useState<LLMConfig>(DEFAULT_LLM_CONFIGS[0]);
  const [blackLLM, setBlackLLM] = useState<LLMConfig>(DEFAULT_LLM_CONFIGS[1]);
  const [showConfig, setShowConfig] = useState(false);

  const handleStart = () => {
    const redPlayer: Player = {
      type: redType,
      side: 'red',
      config: redType === 'llm' ? redLLM : undefined,
    };
    const blackPlayer: Player = {
      type: blackType,
      side: 'black',
      config: blackType === 'llm' ? blackLLM : undefined,
    };
    const gameConfig: GameConfig = {
      redPlayer,
      blackPlayer,
      delayBetweenMoves: 2000,
    };
    newGame(gameConfig);
    onStartGame(gameConfig);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Swords className="w-5 h-5 text-amber-400" />
        <h2 className="text-lg font-bold">對戰配置</h2>
      </div>

      {/* Red Player */}
      <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/5">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="font-semibold">紅方</span>
        </div>
        <div className="flex gap-2 mb-2">
          <button
            onClick={() => setRedType('human')}
            className={`flex items-center gap-1 px-3 py-1 rounded text-sm ${
              redType === 'human' ? 'bg-red-500 text-white' : 'bg-gray-700'
            }`}
          >
            <User className="w-4 h-4" /> 人類
          </button>
          <button
            onClick={() => setRedType('llm')}
            className={`flex items-center gap-1 px-3 py-1 rounded text-sm ${
              redType === 'llm' ? 'bg-red-500 text-white' : 'bg-gray-700'
            }`}
          >
            <Bot className="w-4 h-4" /> AI
          </button>
        </div>
        {redType === 'llm' && (
          <select
            value={redLLM.id}
            onChange={(e) => {
              const cfg = DEFAULT_LLM_CONFIGS.find(c => c.id === e.target.value);
              if (cfg) setRedLLM(cfg);
            }}
            className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm"
          >
            {DEFAULT_LLM_CONFIGS.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        )}
      </div>

      {/* Black Player */}
      <div className="p-4 rounded-lg border border-gray-500/30 bg-gray-500/5">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-3 h-3 rounded-full bg-gray-800 border border-gray-500" />
          <span className="font-semibold">黑方</span>
        </div>
        <div className="flex gap-2 mb-2">
          <button
            onClick={() => setBlackType('human')}
            className={`flex items-center gap-1 px-3 py-1 rounded text-sm ${
              blackType === 'human' ? 'bg-gray-800 text-white border border-gray-500' : 'bg-gray-700'
            }`}
          >
            <User className="w-4 h-4" /> 人類
          </button>
          <button
            onClick={() => setBlackType('llm')}
            className={`flex items-center gap-1 px-3 py-1 rounded text-sm ${
              blackType === 'llm' ? 'bg-gray-800 text-white border border-gray-500' : 'bg-gray-700'
            }`}
          >
            <Bot className="w-4 h-4" /> AI
          </button>
        </div>
        {blackType === 'llm' && (
          <select
            value={blackLLM.id}
            onChange={(e) => {
              const cfg = DEFAULT_LLM_CONFIGS.find(c => c.id === e.target.value);
              if (cfg) setBlackLLM(cfg);
            }}
            className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm"
          >
            {DEFAULT_LLM_CONFIGS.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        )}
      </div>

      {/* Start Button */}
      <button
        onClick={handleStart}
        className="w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-black font-bold py-3 rounded-lg transition-colors"
      >
        <Play className="w-5 h-5" /> 開始對局
      </button>

      {/* Status */}
      {config && (
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">回合</span>
            <span className={`font-bold ${state.turn === 'red' ? 'text-red-400' : 'text-gray-300'}`}>
              {state.turn === 'red' ? '紅方' : '黑方'}
            </span>
          </div>
          {isThinking && (
            <div className="mt-2 text-sm text-amber-400 animate-pulse">
              🤔 {currentLLM} 思考中...
            </div>
          )}
          {state.status !== 'playing' && (
            <div className="mt-2 text-lg font-bold text-center">
              {state.status === 'checkmate' && (
                <span className="text-green-400">
                  🎉 {state.winner === 'red' ? '紅方' : '黑方'} 勝利！
                </span>
              )}
              {state.status === 'stalemate' && <span className="text-gray-400">平局 (困斃)</span>}
              {state.status === 'draw' && <span className="text-gray-400">和棋</span>}
            </div>
          )}
        </div>
      )}

      {/* API Key Config */}
      <button
        onClick={() => setShowConfig(!showConfig)}
        className="text-sm text-gray-500 hover:text-gray-300 underline"
      >
        API Key 設定
      </button>

      {showConfig && (
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700 space-y-2">
          {DEFAULT_LLM_CONFIGS.map(cfg => (
            <div key={cfg.id}>
              <label className="text-xs text-gray-500">{cfg.name} API Key</label>
              <input
                type="password"
                placeholder={`輸入 ${cfg.name} API Key`}
                className="w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm"
                onChange={(e) => {
                  // Store in localStorage
                  localStorage.setItem(`apiKey_${cfg.id}`, e.target.value);
                }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
