'use client';

import { useCallback } from 'react';
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
  // Board is 9 files x 10 ranks
  // Center at origin, scale to fit
  const x = (file - 4) * 1.0;
  const z = (rank - 4.5) * 1.0;
  return [x, 0.1, z];
}

function iccsToSquare(iccs: string): { file: number; rank: number } {
  const fromFile = FILES.indexOf(iccs[0]);
  const fromRank = parseInt(iccs[1], 10);
  return { file: fromFile, rank: fromRank };
}

export function XiangqiBoard3D() {
  const { state, selectedSquare, lastMove, setSelectedSquare, makeMove, getLegalMovesForSquare } = useGame();

  const pieces = parseFEN(state.fen);

  const handlePieceClick = useCallback((piece: string, file: number, rank: number) => {
    const sq = `${FILES[file]}${rank}`;
    const isRed = piece === piece.toUpperCase();
    const currentTurn = state.turn;

    // Can only select own pieces
    if ((currentTurn === 'red' && !isRed) || (currentTurn === 'black' && isRed)) {
      // Maybe it's a capture target
      if (selectedSquare) {
        const move = `${selectedSquare}${sq}`;
        makeMove(move);
      }
      return;
    }

    if (selectedSquare === sq) {
      setSelectedSquare(null);
    } else {
      setSelectedSquare(sq);
    }
  }, [selectedSquare, state.turn, setSelectedSquare, makeMove]);

  const handleBoardClick = useCallback((file: number, rank: number) => {
    if (!selectedSquare) return;
    const sq = `${FILES[file]}${rank}`;
    const move = `${selectedSquare}${sq}`;
    makeMove(move);
  }, [selectedSquare, makeMove]);

  const lastMoveSquares = lastMove ? [lastMove.from, lastMove.to] : [];

  return (
    <group>
      {/* Board base */}
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
      {/* Red palace */}
      <mesh position={[-1, 0.01, 3.5]} rotation={[-Math.PI / 2, 0, Math.PI / 4]}>
        <planeGeometry args={[2.8, 0.02]} />
        <meshBasicMaterial color="#8b4513" />
      </mesh>
      <mesh position={[1, 0.01, 3.5]} rotation={[-Math.PI / 2, 0, -Math.PI / 4]}>
        <planeGeometry args={[2.8, 0.02]} />
        <meshBasicMaterial color="#8b4513" />
      </mesh>
      {/* Black palace */}
      <mesh position={[-1, 0.01, -3.5]} rotation={[-Math.PI / 2, 0, Math.PI / 4]}>
        <planeGeometry args={[2.8, 0.02]} />
        <meshBasicMaterial color="#8b4513" />
      </mesh>
      <mesh position={[1, 0.01, -3.5]} rotation={[-Math.PI / 2, 0, -Math.PI / 4]}>
        <planeGeometry args={[2.8, 0.02]} />
        <meshBasicMaterial color="#8b4513" />
      </mesh>

      {/* Clickable squares */}
      {Array.from({ length: 90 }, (_, i) => {
        const file = i % 9;
        const rank = Math.floor(i / 9);
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
            <meshBasicMaterial
              color={
                selectedSquare === `${FILES[file]}${rank}`
                  ? '#fbbf24'
                  : lastMoveSquares.includes(`${FILES[file]}${rank}`)
                  ? '#22c55e'
                  : 'transparent'
              }
              transparent
              opacity={0.2}
            />
          </mesh>
        );
      })}

      {/* Pieces */}
      {pieces.map((p, i) => (
        <XiangqiPiece
          key={`${p.piece}-${i}`}
          piece={p.piece}
          position={getPosition(p.file, p.rank)}
          isRed={p.piece === p.piece.toUpperCase()}
          isSelected={selectedSquare === `${FILES[p.file]}${p.rank}`}
          isLastMove={lastMoveSquares.includes(`${FILES[p.file]}${p.rank}`)}
          onClick={() => handlePieceClick(p.piece, p.file, p.rank)}
        />
      ))}
    </group>
  );
}
