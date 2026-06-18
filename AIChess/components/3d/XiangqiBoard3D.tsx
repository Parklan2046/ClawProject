'use client';

import { useCallback, useMemo } from 'react';
import { useGame } from '@/hooks/useGame';
import { XiangqiPiece } from './XiangqiPiece';

const FILES = 'abcdefghi';
const RANKS = '0123456789';

function parseFEN(fen: string): { piece: string; file: number; rank: number }[] {
  const pieces: { piece: string; file: number; rank: number }[] = [];
  const [boardPart] = fen.split(' ');
  const ranks = boardPart.split('/');

  ranks.forEach((rankStr, rankIndex) => {
    let fileIndex = 0;
    for (const char of rankStr) {
      if (/\d/.test(char)) {
        fileIndex += parseInt(char, 10);
      } else {
        pieces.push({
          piece: char,
          file: fileIndex,
          rank: rankIndex,
        });
        fileIndex++;
      }
    }
  });

  return pieces;
}

function getPosition(file: number, rank: number): [number, number, number] {
  const x = (file - 4) * 1.0;
  const z = (rank - 4.5) * 1.0;
  return [x, 0.1, z];
}

function squareToFR(sq: string): { file: number; rank: number } {
  return { file: FILES.indexOf(sq[0]), rank: parseInt(sq[1], 10) };
}

export function XiangqiBoard3D() {
  const { state, selectedSquare, lastMove, inCheck, setSelectedSquare, makeMove, getLegalMovesForSquare, legalMoves } = useGame();

  const pieces = parseFEN(state.fen);

  const lastMoveSquares = useMemo(() => {
    if (!lastMove) return [] as string[];
    return [lastMove.from, lastMove.to];
  }, [lastMove]);

  const selectedMoves = useMemo(() => {
    if (!selectedSquare) return [] as string[];
    return getLegalMovesForSquare(selectedSquare);
  }, [selectedSquare, legalMoves, getLegalMovesForSquare]);

  const checkSquare = useMemo(() => {
    if (!inCheck || !state.fen) return null;
    const target = inCheck === 'red' ? 'K' : 'k';
    const [boardPart] = state.fen.split(' ');
    const ranks = boardPart.split('/');
    for (let r = 0; r < 10; r++) {
      let file = 0;
      for (const ch of ranks[r]) {
        if (ch >= '0' && ch <= '9') {
          file += parseInt(ch, 10);
        } else {
          if (ch === target) return { file, rank: r };
          file++;
        }
      }
    }
    return null;
  }, [inCheck, state.fen]);

  const handlePieceClick = useCallback((piece: string, file: number, rank: number) => {
    if (state.status !== 'playing') return;
    const sq = `${FILES[file]}${rank}`;
    const isRed = piece === piece.toUpperCase();
    const currentTurn = state.turn;

    if (selectedSquare) {
      const targetMove = `${selectedSquare}${sq}`;
      const success = makeMove(targetMove);
      if (success) return;
    }

    if ((currentTurn === 'red' && isRed) || (currentTurn === 'black' && !isRed)) {
      setSelectedSquare(sq === selectedSquare ? null : sq);
    } else {
      setSelectedSquare(null);
    }
  }, [selectedSquare, state.turn, state.status, setSelectedSquare, makeMove]);

  const handleBoardClick = useCallback((file: number, rank: number) => {
    if (state.status !== 'playing' || !selectedSquare) return;
    const sq = `${FILES[file]}${rank}`;
    makeMove(`${selectedSquare}${sq}`);
  }, [selectedSquare, state.status, makeMove]);

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]} receiveShadow>
        <boxGeometry args={[10, 11, 0.1]} />
        <meshStandardMaterial color="#f5deb3" roughness={0.8} />
      </mesh>

      {/* Grid lines */}
      {Array.from({ length: 10 }, (_, i) => (
        <mesh key={`h-${i}`} position={[0, 0.01, (i - 4.5) * 1.0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[9, 0.02]} />
          <meshBasicMaterial color="#8b4513" />
        </mesh>
      ))}
      {Array.from({ length: 9 }, (_, i) => (
        <mesh key={`v-${i}`} position={[(i - 4) * 1.0, 0.01, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[0.02, 10]} />
          <meshBasicMaterial color="#8b4513" />
        </mesh>
      ))}

      {/* River */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 0]}>
        <planeGeometry args={[9, 1]} />
        <meshStandardMaterial color="#87ceeb" transparent opacity={0.3} />
      </mesh>

      {/* Palace diagonals */}
      <mesh position={[-1, 0.01, 3.5]} rotation={[-Math.PI / 2, 0, Math.PI / 4]}>
        <planeGeometry args={[2.8, 0.02]} />
        <meshBasicMaterial color="#8b4513" />
      </mesh>
      <mesh position={[1, 0.01, 3.5]} rotation={[-Math.PI / 2, 0, -Math.PI / 4]}>
        <planeGeometry args={[2.8, 0.02]} />
        <meshBasicMaterial color="#8b4513" />
      </mesh>
      <mesh position={[-1, 0.01, -3.5]} rotation={[-Math.PI / 2, 0, Math.PI / 4]}>
        <planeGeometry args={[2.8, 0.02]} />
        <meshBasicMaterial color="#8b4513" />
      </mesh>
      <mesh position={[1, 0.01, -3.5]} rotation={[-Math.PI / 2, 0, -Math.PI / 4]}>
        <planeGeometry args={[2.8, 0.02]} />
        <meshBasicMaterial color="#8b4513" />
      </mesh>

      {/* Clickable squares + selection / last move / check highlights */}
      {Array.from({ length: 90 }, (_, i) => {
        const file = i % 9;
        const rank = Math.floor(i / 9);
        const sqName = `${FILES[file]}${rank}`;
        const isSelected = selectedSquare === sqName;
        const isLast = lastMoveSquares.includes(sqName);
        const isCheck = checkSquare && checkSquare.file === file && checkSquare.rank === rank;
        const color = isCheck
          ? '#ef4444'
          : isSelected
          ? '#fbbf24'
          : isLast
          ? '#22c55e'
          : 'transparent';
        return (
          <mesh
            key={`sq-${i}`}
            position={[(file - 4) * 1.0, 0.01, (rank - 4.5) * 1.0]}
            rotation={[-Math.PI / 2, 0, 0]}
            onClick={(e) => {
              e.stopPropagation();
              handleBoardClick(file, rank);
            }}
          >
            <planeGeometry args={[0.95, 0.95]} />
            <meshBasicMaterial color={color} transparent opacity={isCheck ? 0.45 : 0.2} />
          </mesh>
        );
      })}

      {/* Legal-move hints for the selected piece */}
      {selectedMoves.map((iccs) => {
        const to = squareToFR(iccs.slice(2, 4));
        const x = (to.file - 4) * 1.0;
        const z = (to.rank - 4.5) * 1.0;
        const targetPiece = state.fen
          ? state.fen.split(' ')[0].split('/')[to.rank][to.file]
          : '';
        if (targetPiece) {
          return (
            <mesh
              key={`mv-${iccs}`}
              position={[x, 0.05, z]}
              rotation={[-Math.PI / 2, 0, 0]}
            >
              <ringGeometry args={[0.35, 0.45, 32]} />
              <meshBasicMaterial color="#ef4444" transparent opacity={0.7} />
            </mesh>
          );
        }
        return (
          <mesh
            key={`mv-${iccs}`}
            position={[x, 0.05, z]}
            rotation={[-Math.PI / 2, 0, 0]}
          >
            <cylinderGeometry args={[0.12, 0.12, 0.02, 24]} />
            <meshBasicMaterial color="#22c55e" transparent opacity={0.7} />
          </mesh>
        );
      })}

      {/* Pieces */}
      {pieces.map((p, i) => (
        <XiangqiPiece
          key={`p-${p.piece}-${p.file}-${p.rank}-${i}`}
          piece={p.piece}
          position={getPosition(p.file, p.rank)}
          isRed={p.piece === p.piece.toUpperCase()}
          isSelected={selectedSquare === `${FILES[p.file]}${p.rank}`}
          isLastMove={lastMoveSquares.includes(`${FILES[p.file]}${p.rank}`)}
          isInCheck={Boolean(checkSquare && checkSquare.file === p.file && checkSquare.rank === p.rank)}
          onClick={() => handlePieceClick(p.piece, p.file, p.rank)}
        />
      ))}
    </group>
  );
}
