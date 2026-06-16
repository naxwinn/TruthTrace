"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface ParticlesProps {
  count?: number;
}

export function Particles({ count = 2000 }: ParticlesProps) {
  const ref = useRef<THREE.Points>(null);

  const { positions, sizes, colors } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const siz = new Float32Array(count);
    const col = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 120;
      pos[i * 3 + 1] = Math.random() * 30;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 120 - 20;

      siz[i] = Math.random() * 0.08 + 0.02;

      // Mostly cyan with occasional amber
      if (Math.random() > 0.85) {
        col[i * 3] = 1.0;
        col[i * 3 + 1] = 0.42;
        col[i * 3 + 2] = 0.17;
      } else {
        col[i * 3] = 0;
        col[i * 3 + 1] = 0.7 + Math.random() * 0.3;
        col[i * 3 + 2] = 1.0;
      }
    }

    return { positions: pos, sizes: siz, colors: col };
  }, [count]);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    const posAttr = ref.current.geometry.attributes.position;

    for (let i = 0; i < count; i++) {
      const idx = i * 3;
      // Gentle drift upward
      posAttr.array[idx + 1] += 0.003;

      // Reset if too high
      if (posAttr.array[idx + 1] > 30) {
        posAttr.array[idx + 1] = -2;
      }

      // Subtle horizontal sway
      posAttr.array[idx] += Math.sin(t * 0.5 + i) * 0.002;
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={count}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        vertexColors
        transparent
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
}
