'use client';

import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import { XiangqiBoard3D } from './XiangqiBoard3D';

export function Scene() {
  return (
    <div className="w-full h-full min-h-[500px]">
      <Canvas camera={{ position: [0, 12, 8], fov: 45 }} shadows>
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 10, 5]} intensity={1} castShadow />
        <pointLight position={[-5, 5, -5]} intensity={0.4} />
        <Environment preset="wood" />
        <XiangqiBoard3D />
        <OrbitControls
          maxPolarAngle={Math.PI / 2.2}
          minPolarAngle={Math.PI / 6}
          maxDistance={20}
          minDistance={5}
          target={[0, 0, 0]}
        />
      </Canvas>
    </div>
  );
}
