"use client";

import { Canvas } from "@react-three/fiber";
import { Suspense } from "react";
import { Landscape } from "./Landscape";
import { FloatingElements } from "./FloatingElements";
import { AudioAbyss } from "./AudioAbyss";
import { VisualRift } from "./VisualRift";
import { MetadataCore } from "./MetadataCore";
import { Particles } from "./Particles";
import { CameraController } from "./CameraController";
import { Environment } from "@react-three/drei";

export function Scene() {
  return (
    <div className="fixed inset-0 z-0">
      <Canvas
        camera={{ position: [0, 5, 20], fov: 60, near: 0.1, far: 500 }}
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 2]}
      >
        <Suspense fallback={null}>
          <fog attach="fog" args={["#050508", 30, 150]} />
          <ambientLight intensity={0.15} />
          <directionalLight
            position={[10, 20, 10]}
            intensity={0.3}
            color="#4488ff"
          />
          <pointLight position={[-10, 10, -10]} intensity={0.5} color="#00f0ff" />
          <pointLight position={[15, 5, -20]} intensity={0.3} color="#ff6b2b" />

          <CameraController />
          <Landscape />
          <FloatingElements />
          <AudioAbyss />
          <VisualRift />
          <MetadataCore />
          <Particles count={2000} />

          <Environment preset="night" />
        </Suspense>
      </Canvas>
    </div>
  );
}
