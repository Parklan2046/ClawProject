'use client';

import { useGame } from '@/hooks/useGame';
import { History } from 'lucide-react';
import { PIECE_NAMES } from '@/lib/constants';

export function MoveHistory() {
  const { state, lastMove } = useGame();

  const lastPieceName = lastMove?.piece ? (PIECE_NAMES[lastMove.piece] || lastMove.piece) : '';
  const lastCapturedName = lastMove?.captured ? (PIECE_NAMES[lastMove.captured] || lastMove.captured) : '';

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-2">
        <History className="w-5 h-5 text-amber-400" />
        <h2 className="text-lg font-bold">棋譜</h2>
      </div>

      <div className="h-64 overflow-y-auto rounded-lg border border-gray-700 bg-gray-800/30">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-gray-800">
            <tr>
              <th className="px-2 py-1 text-left text-gray-500">#</th>
              <th className="px-2 py-1 text-left text-red-400">紅方</th>
              <th className="px-2 py-1 text-left text-gray-400">黑方</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: Math.ceil(state.history.length / 2) }, (_, i) => {
              const redMove = state.history[i * 2];
              const blackMove = state.history[i * 2 + 1];
              return (
                <tr key={i} className="border-t border-gray-700/50 hover:bg-gray-700/30">
                  <td className="px-2 py-1 text-gray-500">{i + 1}</td>
                  <td className="px-2 py-1 font-mono text-red-300">{redMove || '-'}</td>
                  <td className="px-2 py-1 font-mono text-gray-300">{blackMove || '-'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {state.history.length === 0 && (
          <div className="p-4 text-center text-gray-500 text-sm">尚無棋步</div>
        )}
      </div>

      {lastMove && (
        <div className="p-2 rounded bg-amber-500/10 border border-amber-500/30">
          <div className="text-xs text-gray-500">最新棋步</div>
          <div className="font-mono text-amber-400">
            {lastPieceName} {lastMove.from} → {lastMove.to}
            {lastCapturedName && <span className="text-red-400"> 吃 {lastCapturedName}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
