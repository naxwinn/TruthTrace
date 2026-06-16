"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

function GlitchCrystal({ position, scale }: { position: [number, number, number]; scale: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const glitchOffset = useRef(0);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.getElapsedTime();

    // Periodic glitch effect
    if (Math.random() < 0.02) {
      glitchOffset.current = (Math.random() - 0.5) * 0.5;
    } else {
      glitchOffset.current *= 0.9;
    }

    meshRef.current.position.x = position[0] + glitchOffset.current;
    meshRef.current.rotation.y = t * 0.2;
    meshRef.current.rotation.x = Math.sin(t * 0.3) * 0.1;

    const mat = meshRef.current.material as THREE.MeshStandardMaterial;
    mat.emissiveIntensity = 0.3 + Math.abs(glitchOffset.current) * 2;
  });

  return (
    <mesh ref={meshRef} position={position} scale={scale}>
      <icosahedronGeometry args={[1, 1]} />
      <meshStandardMaterial
        color="#ff2b4e"
        emissive="#ff6b2b"
        emissiveIntensity={0.3}
        transparent
        opacity={0.8}
        roughness={0.2}
        metalness={0.9}
        wireframe={Math.random() > 0.5}
      />
    </mesh>
  );
}

function OpticalFlowVis() {
  const ref = useRef<THREE.Points>(null);

  const { positions, colors } = useMemo(() => {
    const count = 500;
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const r = 2 + Math.random() * 6;
      pos[i * 3] = Math.cos(theta) * r;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 4;
      pos[i * 3 + 2] = Math.sin(theta) * r;

      // Color gradient from cyan to red based on radius
      const t = r / 8;
      col[i * 3] = t;
      col[i * 3 + 1] = (1 - t) * 0.9;
      col[i * 3 + 2] = (1 - t);
    }

    return { positions: pos, colors: col };
  }, []);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    const posAttr = ref.current.geometry.attributes.position;

    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getZ(i);
      const angle = Math.atan2(z, x) + t * 0.2;
      const r = Math.sqrt(x * x + z * z);
      posAttr.setX(i, Math.cos(angle) * r);
      posAttr.setZ(i, Math.sin(angle) * r);
      posAttr.setY(i, posAttr.getY(i) + Math.sin(t + i * 0.1) * 0.005);
    }
    posAttr.needsUpdate = true;
    ref.current.rotation.y = t * 0.05;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} count={positions.length / 3} itemSize={3} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} count={colors.length / 3} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.06} vertexColors transparent opacity={0.7} sizeAttenuation />
    </points>
  );
}

export function VisualRift() {
  const crystals = useMemo(
    () => [
      { position: [0, 2, 0] as [number, number, number], scale: 1.2 },
      { position: [-3, 1, -2] as [number, number, number], scale: 0.8 },
      { position: [2.5, 3, -1] as [number, number, number], scale: 0.6 },
      { position: [-1.5, 4, 1] as [number, number, number], scale: 0.5 },
      { position: [3, 0.5, 2] as [number, number, number], scale: 0.7 },
      { position: [-2, 3.5, -3] as [number, number, number], scale: 0.4 },
    ],
    []
  );

  return (
    <group position={[0, 6, -55]}>
      {crystals.map((props, i) => (
        <GlitchCrystal key={i} {...props} />
      ))}
      <OpticalFlowVis />
      <pointLight position={[0, 3, 0]} intensity={2} color="#ff6b2b" distance={15} />
      <pointLight position={[-3, 1, 0]} intensity={1} color="#ff2b4e" distance={10} />
    </group>
  );
}
