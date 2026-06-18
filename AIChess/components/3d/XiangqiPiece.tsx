'use client';

import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, RoundedBox } from '@react-three/drei';
import * as THREE from 'three';
import { PIECE_NAMES } from '@/lib/constants';

interface PieceProps {
  piece: string;
  position: [number, number, number];
  isRed: boolean;
  isSelected?: boolean;
  isLastMove?: boolean;
  isInCheck?: boolean;
  onClick?: () => void;
}

export function XiangqiPiece({ piece, position, isRed, isSelected, isLastMove, isInCheck, onClick }: PieceProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  useFrame((_, delta) => {
    if (meshRef.current) {
      const targetY = isSelected ? 0.4 : 0;
      meshRef.current.position.y = THREE.MathUtils.lerp(meshRef.current.position.y, position[1] + targetY, delta * 10);
    }
  });

  const baseColor = isRed ? '#dc2626' : '#1f1f1f';
  const color = isInCheck ? '#fca5a5' : hovered ? '#fbbf24' : baseColor;
  const emissive = isInCheck ? '#ef4444' : isSelected ? '#fbbf24' : isLastMove ? '#22c55e' : '#000000';
  const emissiveIntensity = isInCheck ? 0.8 : isSelected ? 0.5 : isLastMove ? 0.3 : 0;

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation();
          onClick?.();
        }}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        castShadow
        receiveShadow
      >
        <cylinderGeometry args={[0.35, 0.4, 0.2, 32]} />
        <meshStandardMaterial
          color={hovered ? '#fbbf24' : color}
          emissive={emissive}
          emissiveIntensity={emissiveIntensity}
          roughness={0.3}
          metalness={0.6}
        />
      </mesh>
      <Text
        position={[0, 0.11, 0]}
        fontSize={0.35}
        color={isRed ? '#fef2f2' : '#d4d4d8'}
        anchorX="center"
        anchorY="middle"
        font="/fonts/NotoSansSC-Bold.woff"
      >
        {PIECE_NAMES[piece] || piece}
      </Text>
      {/* Selection ring */}
      {isSelected && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
          <ringGeometry args={[0.45, 0.55, 32]} />
          <meshBasicMaterial color="#fbbf24" transparent opacity={0.8} />
        </mesh>
      )}
    </group>
  );
}
